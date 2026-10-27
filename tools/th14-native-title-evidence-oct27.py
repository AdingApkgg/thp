"""Verify finite actual-native title buffers and retain the open failures.

Reads existing captures/builds only. No original game or browser is launched.
The output contains source hashes and observations, never game assets, pixels
or raw native memory. Exact finite frames do not certify the complete game.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,struct

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--home',type=Path,default=ROOT/'artifacts/th14/native-frame-readback-oct27')
    p.add_argument('--output',type=Path,default=ROOT/'docs/porting/th14-native-title-verified-oct27.json')
    p.add_argument('--check',action='store_true');a=p.parse_args();home=a.home.resolve();output=a.output.resolve()
    assert home.is_relative_to(ROOT/'artifacts/th14')and output.is_relative_to(ROOT)
    bindings={}
    def bind(path):
        path=path.resolve();assert path.is_relative_to(ROOT);raw=path.read_bytes()
        bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def read(path):return json.loads(bind(path))
    for name in ['tools/th14-build-native-application.py','tools/th14-native-application-process-host-oct27.py',
        'tools/th14-native-device-observer-oct27.py','tools/th14-native-frame-readback-program-oct27.py',
        'tools/th14-native-fps-guard-oct27.py','tools/th14-native-title-idle-guard-oct27.py',
        'tools/th14-native-title-image-compare-oct27.py','tools/th14-native-title-live-compare-oct27.py',
        'runtimes/th12/th12_web/tests/cpp/th14-native-title-fixture.cpp',
        'runtimes/th12/th12_web/tests/cpp/th14-native-title-live-observer.hpp',
        'runtimes/th12/th12_web/cpp/sdl/Application.cpp','runtimes/th12/th12_web/cpp/game/GameSession.cpp']:
        bind(ROOT/name)
    abi=read(home/'program-abi.json');assert abi['abiControlsPassed']and len(abi['cases'])==18
    assert abi['helperSha256']==SHA(bind(ROOT/'tools/th14-native-frame-readback-program-oct27.py'))
    fps=read(home/'fps-guard/native.json');idle=read(home/'idle-guard/native.json')
    assert fps['actualGuardCases']==16 and fps['originalSkipModes']==[4,15]and idle['actualGuardCases']==36
    for name,tool in [('fps-guard','th14-native-fps-guard-oct27.py'),('idle-guard','th14-native-title-idle-guard-oct27.py')]:
        r=read(home/name/'native.json');assert r['sourceSha256']==SHA(bind(home/name/'run-tool.py'))==SHA(bind(ROOT/'tools'/tool))
    for name in ('idle-gles-build','idle-webgpu-build'):
        b=read(home/name/'build.json');assert b['compiled']and b['readOnlyReferenceStateExport']
        assert SHA(bind(home/name/'application.wasm'))==b['wasmSha256']
        for path,row in b['sourceBindings'].items():assert SHA(bind(ROOT/path))==row['sha256'],path
        for row in b['coreObjects']:assert SHA(bind(Path(row['path'])))==row['sha256']
        for path,digest in b.get('reusedPlatformObjects',{}).items():assert SHA(bind(ROOT/path))==digest
        for path,digest in b['newObjects'].items():assert SHA(bind(home/name/path))==digest
    core=read(home/'idle-core-build/observer-build.json')
    assert core['engineSourcesRecompiledForThisLink']==1 and core['engineObjectsReusedForThisLink']==140
    assert core['sourceHashes']['th12_web/cpp/game/GameSession.cpp']==SHA(bind(ROOT/'runtimes/th12/th12_web/cpp/game/GameSession.cpp'))
    frames=[]
    for native_name,port_name in [('present-0240','title240-idle-after-gles'),
        ('present-0420-vms','title420-idle-after-gles'),('present-0420-vms','title420-idle-after-webgpu')]:
        n=read(home/native_name/'report.json');r=read(home/port_name/'report.json')
        assert n['frameReadbackCompleted']and n['childExited']and not n['error']and r['completed']and not r['error']
        assert n['diagnosticPrivateCodeAllocated']and n['threadContextRedirects']==2 and n['gameNeverResumedAfterReadback']
        assert n['readback']['statusesAtCaptureStop'][:5]==[0]*5 and n['readback']['cleanupResults']==[0,0,1]
        assert n['readback']['surfaceDescription']==[21,1,1,0,0,0,640,480]
        assert n['sourceSha256']==SHA(bind(home/native_name/'run-tool.py'))
        assert r['toolSha256']==SHA(bind(home/port_name/'run-tool.py'))
        ordinal=n['plan']['capturePresentOrdinal'];s=next(x for x in n['rows']if x.get('kind')=='native-Present-entry'and x['ordinal']==ordinal)
        assert s['supervisorWords']==[4,4]and s['readBeforeDiagnosticCalls']and len(r['captures'])==1
        c=r['captures'][0];rng=struct.unpack('<HHIHHI',bytes.fromhex(s['rngHex']))
        assert c['referenceState'][:7]==[s['originalInitialTicks'],s['originalProcessCookie'],s['idleCounter'],rng[0],rng[2],rng[3],rng[5]]
        left=bind(home/native_name/n['readback']['file']);right=bind(home/port_name/c['file'])
        assert len(left)==len(right)==1228800 and left==right
        assert SHA(left)==n['readback']['pixelSha256']==c['sha256']
        frames.append(dict(nativePresent=ordinal,titleIdle=s['idleCounter'],backend=r['backend'],
            portApplicationFrame=r['frames'],bytesCompared=len(left),sha256=SHA(left),differentBytes=0))
    before=read(home/'title-comparison.json');middle=read(home/'title420-vms-pixel-comparison.json')
    assert before['differentPixels']==203 and before['differentBytes']==630
    assert middle['differentPixels']==27980 and middle['differentBytes']==47122
    strict=read(home/'title420-idle-after-vms-comparison.json')
    assert not strict['allLiveValuesEqual']and strict['differenceCount']==62
    n=read(home/'present-0420-vms/live-vms-before-readback.json');r=read(home/'title420-idle-after-gles/report.json')
    cap=r['captures'][0];raw=bind(home/'title420-idle-after-gles'/cap['liveAnimations']['file'])
    assert SHA(raw)==cap['liveAnimations']['sha256'];v=json.loads(raw)
    spec=importlib.util.spec_from_file_location('title_words',ROOT/'tools/th14-native-title-live-compare-oct27.py')
    compare=importlib.util.module_from_spec(spec);spec.loader.exec_module(compare)
    address={struct.unpack_from('<I',bytes.fromhex(x['rawVmHex']),0x570)[0]:x['handle']for x in n['rows']}
    native={(x['file'],x['script']):x for x in n['rows']};port={(x[1],x[2]):x for x in v['rows']}
    assert len(native)==len(port)==len(n['rows'])==len(v['rows'])==30 and set(native)==set(port)
    remap={native[k]['handle']:port[k][0]for k in native};links={'handle','parentHandle','registryNextHandle','registryPreviousHandle','childNextHandle','childPreviousHandle'}
    remaining=[]
    for key in native:
        names,words=compare.native_words(native[key],address)
        for field,left,right in zip(names,words,port[key]):
            if field in links:left=remap.get(left,left)
            if left!=right:remaining.append(dict(file=key[0],script=key[1],field=field,native=left,portable=right))
    assert remaining==[dict(file=16,script=0,field='nativeVmWord0x24',native=0,portable=22)]
    g=read(home/'idle-demo-gles/report.json');w=read(home/'idle-demo-webgpu/report.json')
    assert g['completed']and w['completed']and g['frames']==w['frames']==2265
    assert len(g['checks'])==7 and all(x['passed']for x in g['checks'])and g['checks']==w['checks']
    assert g['rows']==w['rows']and len(g['rows'])==131 and g['finalSave']==w['finalSave']
    assert g['pcmFrames']==w['pcmFrames']==1508352 and g['pcmSha256']==w['pcmSha256']
    diffs=[]
    for x,y in zip(g['captures'],w['captures']):
        left=bind(home/'idle-demo-gles'/x['file']);right=bind(home/'idle-demo-webgpu'/y['file'])
        assert SHA(left)==x['sha256']and SHA(right)==y['sha256']
        changed=[i for i,(a,b)in enumerate(zip(left,right))if a!=b]
        diffs.append(dict(label=x['label'],differentBytes=len(changed),differentPixels=len({i//4 for i in changed}),
            first=[dict(x=i//4%640,y=i//2560,channel=i%4,gles=left[i],webgpu=right[i])for i in changed[:8]]))
    assert [x['differentBytes']for x in diffs]==[0,2]
    result=dict(schema='th14/actual-native-title-finite-evidence/1',verifiedFiniteTitleFrames=True,
        actualNativeBuffers=2,exactBackendComparisons=frames,nativeReadbackAbiControls=18,nativeFpsGuardCases=16,nativeIdleGuardCases=36,
        fpsBeforeDifferentPixels=203,fpsBeforeDifferentBytes=630,titleIdleBeforeDifferentPixels=27980,titleIdleBeforeDifferentBytes=47122,
        pixelTolerance=0,alphaExcluded=False,originalProcessInstrumentationDeclared=True,nativePrivateCodeAndTwoContextRedirects=True,
        originalInstructionsGameFieldsRngAndInputUnwritten=True,nativeChildrenExited=True,readbackResourcesReleased=True,
        strictLiveVmComparisonPassed=False,strictLiveVmDifferenceCount=62,
        exploratoryUniqueFileScriptPairs=30,explicitHandleRemapUsedOnlyForExploratoryLinkComparison=True,
        remainingSemanticVmDifferences=remaining,exploratoryRemapIsNotStrictAcceptance=True,
        affectedDemoPrefixFrames=2265,demoAssertions=7,demoJournalRows=131,demoSilentPcmFrames=1508352,
        demoStateFilesAndPcmBackendEqual=True,demoImageBackendComparisonPassed=False,demoImages=diffs,
        failuresRetained=True,ordinaryOriginalUiAccepted=False,nativeNaturalRunModePairs=30,nativeAllStageEntryModePairs=25,
        physicalAudioDevicesOpened=0,completeGame=False,nativeEquivalent=False,browserAcceptance=False,
        verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)
    encoded=json.dumps(result,indent=2)+'\n'
    if a.check:assert output.read_text()==encoded,'Evidence differs; inspect before replacing'
    else:output.write_text(encoded)
    print(json.dumps({k:v for k,v in result.items()if k not in ('bindings','exactBackendComparisons','remainingSemanticVmDifferences','demoImages')}))


if __name__=='__main__':main()
