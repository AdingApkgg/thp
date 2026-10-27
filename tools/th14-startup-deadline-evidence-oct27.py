"""Verify finite startup evidence and retain the alternate-schedule failure.

This checks actual native observations against the unchanged production C++.
The test host declares a deadline clock and zero callback execution duration;
it does not reproduce arbitrary native worker interleavings.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,struct

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--home',type=Path,default=ROOT/'artifacts/th14/native-frame-readback-oct27')
    p.add_argument('--output',type=Path,default=ROOT/'docs/porting/th14-startup-deadline-verified-oct27.json')
    p.add_argument('--check',action='store_true');a=p.parse_args();home=a.home.resolve();out=a.output.resolve()
    assert home.is_relative_to(ROOT/'artifacts/th14')and out.is_relative_to(ROOT);bindings={}
    def read(path):
        path=path.resolve();assert path.is_relative_to(ROOT);raw=path.read_bytes()
        bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def load(path):return json.loads(read(path))
    host=read(ROOT/'tools/th14-native-application-process-host-oct27.py')
    for name in ('tools/th14-build-native-application.py','runtimes/th12/th12_web/tests/cpp/th14-native-title-fixture.cpp',
                 'tools/th14-native-title-live-compare-oct27.py','tools/th14-native-title-image-compare-oct27.py'):
        read(ROOT/name)
    assert b'clock_ns=due'in host and b'max(1,delay)'in host
    spec=importlib.util.spec_from_file_location('startup_live_words',ROOT/'tools/th14-native-title-live-compare-oct27.py')
    compare=importlib.util.module_from_spec(spec);spec.loader.exec_module(compare)
    def native(name,with_vms=True):
        n=home/name;r=load(n/'report.json')
        assert r['childExited']and r['frameReadbackCompleted']and not r['error']
        assert r['sourceSha256']==SHA(read(n/'run-tool.py'))
        assert r['originalCodeWrites']==0 and r['gameStateWrites']==0 and not r['inputInjection']
        assert r['readback']['statusesAtCaptureStop'][:5]==[0]*5 and r['readback']['cleanupResults']==[0,0,1]
        ordinal=r['plan']['capturePresentOrdinal']
        s=next(x for x in r['rows']if x['kind']=='native-Present-entry'and x['ordinal']==ordinal)
        v=load(n/'live-vms-before-readback.json')if with_vms else None
        if with_vms:assert v['readOnly']and v['readBeforeDiagnosticCalls']and v['ordinaryAndOverlayRegistryWalk']
        pixels=read(n/r['readback']['file']);assert len(pixels)==1228800
        return r,s,v,pixels
    nr,ns,nv,np=native('present-0420-publications')
    assert len(nr['animationPublications'])==80 and ns['idleCounter']==232
    publications=[[x[k]for k in ('handle','file','script')]for x in nr['animationPublications']]
    assert [x['serial']for x in nr['animationPublications']]==list(range(1,81))
    by_address={struct.unpack_from('<I',bytes.fromhex(x['rawVmHex']),0x570)[0]:x['handle']for x in nv['rows']}
    expected=[]
    for row in nv['rows']:
        fields,words=compare.native_words(row,by_address);expected.append(words)
    assert len(expected)==30 and all(len(x)==303 for x in expected)
    rng=struct.unpack('<HHIHHI',bytes.fromhex(ns['rngHex']))
    reference=[ns['originalInitialTicks'],ns['originalProcessCookie'],232,rng[0],rng[2],rng[3],rng[5]]
    builds={};runs={}
    for backend,build_name,run_name in [('webgpu','deadline-observer-webgpu-build-v2','deadline232-observed-public'),
                                         ('gles','deadline-observer-gles-build','deadline232-observed-gles')]:
        b=home/build_name;build=load(b/'build.json');builds[backend]=build
        assert build['compiled']and build['backend']==backend
        assert SHA(read(b/'application.wasm'))==build['wasmSha256']
        assert 'component_births'in build['exports']and build['birthExportReadOnly']
        for path,row in build['sourceBindings'].items():assert SHA(read(ROOT/path))==row['sha256'],path
        for row in build['coreObjects']:assert SHA(read(Path(row['path'])))==row['sha256']
        for path,digest in build['reusedPlatformObjects'].items():assert SHA(read(ROOT/path))==digest
        for path,digest in build['newObjects'].items():assert SHA(read(b/path))==digest
        assert len(build['coreObjects'])==141 and len(build['reusedPlatformObjects'])==4
        r=load(home/run_name/'report.json');runs[backend]=r
        assert r['completed']and not r['error']and r['frames']==415 and len(r['checks'])==4
        assert r['wasmSha256']==build['wasmSha256']and r['buildReportSha256']==SHA(read(b/'build.json'))
        assert r['toolSha256']==SHA(read(home/run_name/'run-tool.py'))==SHA(host)
        assert r['minimumCallbackDelayMs']==1 and 'execution duration declared zero'in r['callbackClockPolicy']
        assert r['physicalAudioDevicesOpened']==0 and not r['productionChanged']and not r['browserAcceptance']
        births=sorted(r['animationCreationRecords'],key=lambda x:x['serial'])
        assert [[x[k]for k in ('handle','file','script')]for x in births]==publications
        assert len(r['captures'])==1;c=r['captures'][0];assert c['referenceState'][:7]==reference
        assert read(home/run_name/c['file'])==np
        raw=read(home/run_name/c['liveAnimations']['file']);assert SHA(raw)==c['liveAnimations']['sha256']
        v=json.loads(raw);assert v['complete']and v['expected']==30 and v['comparedValues']==303
        assert v['rows']==expected # Direct handles and registry order; no pairing or handle mapping.
    alternate,asnap,av,ap=native('startup-ready-boundaries',with_vms=False)
    negative_name='deadline20-observed-public';negative=load(home/negative_name/'report.json')
    assert negative['completed']and not negative['error']and negative['frames']==203
    assert negative['toolSha256']==SHA(read(home/negative_name/'run-tool.py'))==SHA(host)
    assert negative['wasmSha256']==builds['webgpu']['wasmSha256']
    c=negative['captures'][0];arng=struct.unpack('<HHIHHI',bytes.fromhex(asnap['rngHex']))
    assert c['referenceState'][:3]==[asnap['originalInitialTicks'],asnap['originalProcessCookie'],20]
    assert read(home/negative_name/c['file'])==ap
    assert len(alternate['animationPublications'])==56 and len(negative['animationCreationRecords'])==57
    assert [arng[0],arng[2]]==[29574,1316]and c['referenceState'][3:5]==[4693,1340]
    assert c['referenceState'][5:7]==[arng[3],arng[5]]
    demos={}
    for backend in ('webgpu','gles'):
        name='deadline-demo-'+backend;r=load(home/name/'report.json');demos[backend]=r
        assert r['completed']and not r['error']and r['frames']==2264 and len(r['checks'])==7
        assert r['wasmSha256']==builds[backend]['wasmSha256']and r['toolSha256']==SHA(read(home/name/'run-tool.py'))==SHA(host)
        assert r['physicalAudioDevicesOpened']==0 and r['declaredInitialGameTicks']==reference[0]
        assert len(r['captures'])==2 and r['pcmFrames']==1508352
    for field in ('rows','actions','checks','initialSave','finalSave','files','pcmFrames','pcmSha256','finalReferenceState'):
        assert demos['webgpu'][field]==demos['gles'][field],field
    for x,y in zip(demos['webgpu']['captures'],demos['gles']['captures']):
        assert x==y
        for field in ('file',):assert read(home/'deadline-demo-webgpu'/x[field])==read(home/'deadline-demo-gles'/y[field])
        assert read(home/'deadline-demo-webgpu'/x['liveAnimations']['file'])==read(home/'deadline-demo-gles'/y['liveAnimations']['file'])
    result=dict(schema='th14/startup-deadline-finite-evidence/1',verifiedGeneralHostDeadlineCorrection=True,
        productionGameplayChanged=False,productionBrowserSchedulerChanged=False,minimumCallbackDelayMs=1,
        callbackExecutionDurationDeclaredZero=True,callbackKindSpecificBranchesAdded=False,
        exactNativePresent=420,titleIdle=232,cppApplicationFrames=415,backends=['gles','webgpu'],
        all80PublicationHandlesFilesAndScriptsExact=True,all30LiveVms303WordsAndRegistryOrderExact=True,
        comparedLiveWords=9090,handleRemappingUsed=False,bothRngSeedsAndCountsExact=True,all1228800BgraBytesExact=True,
        nativeReadbackPrivateCodeAndTwoContextRedirectsDeclared=True,originalGameCodeFieldsAndInputUnwritten=True,
        alternateStartupFailed=True,alternateNativePresent=210,alternateTitleIdle=20,
        alternateNativeBirths=56,alternateCppBirths=57,alternateNativeScriptCalls=1316,alternateCppScriptCalls=1340,
        alternatePixelEqualityDoesNotOverrideRngAndPublicationFailure=True,
        actualDemoFramesPerBackend=2264,assertionsPerBackend=7,journalRowsPerBackend=len(demos['gles']['rows']),
        silentPcmFramesPerBackend=1508352,demoImagesStateFilesAndPcmEqualBetweenBackends=True,
        fullPreviousCampaignResultsInherited=False,oldFailuresRetained=True,nativeChildrenExited=True,
        physicalInputAndOrdinaryNativeUiAccepted=False,nativeNaturalRunModePairs=30,nativeAllStageEntryModePairs=25,
        completeGame=False,nativeEquivalent=False,browserAcceptance=False,
        verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)
    encoded=json.dumps(result,indent=2)+'\n'
    if a.check:assert out.read_text()==encoded
    else:out.write_text(encoded)
    print(json.dumps({k:v for k,v in result.items()if k!='bindings'}))


if __name__=='__main__':main()
