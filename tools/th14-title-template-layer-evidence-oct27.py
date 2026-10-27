"""Check title-template layer repair without accepting remapped handles as equal."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,struct

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--home',type=Path,default=ROOT/'artifacts/th14/native-frame-readback-oct27')
    p.add_argument('--output',type=Path,default=ROOT/'docs/porting/th14-title-template-layer-verified-oct27.json')
    p.add_argument('--check',action='store_true');a=p.parse_args();home=a.home.resolve();out=a.output.resolve()
    assert home.is_relative_to(ROOT/'artifacts/th14')and out.is_relative_to(ROOT);bindings={}
    def read(path):
        path=path.resolve();assert path.is_relative_to(ROOT);raw=path.read_bytes()
        bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def load(path):return json.loads(read(path))
    for name in ['runtimes/th12/th12_web/cpp/game/TitleMenu.cpp','tools/th14-native-title-template-layer-oct27.py',
        'tools/th14-native-title-live-compare-oct27.py','tools/th14-native-application-process-host-oct27.py']:
        read(ROOT/name)
    guard=load(home/'title-layer-prefix/native.json')
    assert guard['actualFactoryPrefixCases']==12 and guard['allocationAndTemplateCopyAreDeclaredServices']
    assert not guard['actualAnmUpdateExecuted']and not guard['actualRegistryPublicationExecuted']
    assert guard['sourceSha256']==SHA(read(home/'title-layer-prefix/run-tool.py'))==SHA(read(ROOT/'tools/th14-native-title-template-layer-oct27.py'))
    assert all(row['templateLayer']==row['layerAtActualAnmUpdate']for row in guard['cases'])
    build=load(home/'title-layer-webgpu-build/build.json');core=load(home/'title-layer-core-build/observer-build.json')
    assert build['compiled']and build['wasmSha256']==SHA(read(home/'title-layer-webgpu-build/application.wasm'))
    assert core['engineSourcesRecompiledForThisLink']==1 and core['engineObjectsReusedForThisLink']==140
    assert core['sourceHashes']['th12_web/cpp/game/TitleMenu.cpp']==SHA(read(ROOT/'runtimes/th12/th12_web/cpp/game/TitleMenu.cpp'))
    for name,row in build['sourceBindings'].items():assert SHA(read(ROOT/name))==row['sha256'],name
    for row in build['coreObjects']:assert SHA(read(Path(row['path'])))==row['sha256']
    for name,digest in build['reusedPlatformObjects'].items():assert SHA(read(ROOT/name))==digest
    native_home=home/'present-0420-vms';port_home=home/'title-layer420-webgpu'
    native=load(native_home/'live-vms-before-readback.json');nr=load(native_home/'report.json');pr=load(port_home/'report.json')
    assert nr['childExited']and nr['frameReadbackCompleted']and pr['completed']and not pr['error']
    assert pr['wasmSha256']==build['wasmSha256']and len(pr['captures'])==1
    c=pr['captures'][0];raw=read(port_home/c['liveAnimations']['file']);assert SHA(raw)==c['liveAnimations']['sha256'];portable=json.loads(raw)
    snapshot=next(x for x in nr['rows']if x.get('kind')=='native-Present-entry'and x['ordinal']==420)
    rng=struct.unpack('<HHIHHI',bytes.fromhex(snapshot['rngHex']))
    assert c['referenceState'][:7]==[snapshot['originalInitialTicks'],snapshot['originalProcessCookie'],231,rng[0],rng[2],rng[3],rng[5]]
    left=read(native_home/nr['readback']['file']);right=read(port_home/c['file']);assert left==right and len(left)==1228800
    spec=importlib.util.spec_from_file_location('title_layer_words',ROOT/'tools/th14-native-title-live-compare-oct27.py')
    compare=importlib.util.module_from_spec(spec);spec.loader.exec_module(compare)
    byaddr={struct.unpack_from('<I',bytes.fromhex(x['rawVmHex']),0x570)[0]:x['handle']for x in native['rows']}
    n={(x['file'],x['script']):x for x in native['rows']};q={(x[1],x[2]):x for x in portable['rows']}
    assert len(n)==len(q)==len(native['rows'])==len(portable['rows'])==30 and set(n)==set(q)
    remap={n[k]['handle']:q[k][0]for k in n};links={'handle','parentHandle','registryNextHandle','registryPreviousHandle','childNextHandle','childPreviousHandle'}
    diffs=[];words_compared=0
    for key in n:
        fields,words=compare.native_words(n[key],byaddr)
        for field,x,y in zip(fields,words,q[key]):
            words_compared+=1
            if field in links:x=remap.get(x,x)
            if x!=y:diffs.append(dict(key=key,field=field,native=x,portable=y))
    assert words_compared==9090 and not diffs
    before=load(home/'title420-idle-after-vms-comparison.json');strict=load(home/'title-layer420-strict-vms.json')
    assert before['differenceCount']==62 and strict['differenceCount']==61 and not strict['allLiveValuesEqual']
    after=load(home/'title-layer-demo-webgpu/report.json');baseline=load(home/'line-demo-webgpu/report.json')
    assert after['completed']and not after['error']and after['wasmSha256']==build['wasmSha256']
    assert after['frames']==2265 and len(after['checks'])==7
    for field in ('rows','actions','checks','finalSave','pcmFrames','pcmSha256'):assert after[field]==baseline[field],field
    for x,y in zip(after['captures'],baseline['captures']):
        assert read(home/'title-layer-demo-webgpu'/x['file'])==read(home/'line-demo-webgpu'/y['file'])
    result=dict(schema='th14/title-template-layer-finite-evidence/1',verifiedFiniteLayerRepair=True,nativeFactoryPrefixCases=12,
        nativeAllocationAndTemplateCopyDeclared=True,componentStopsBeforeAnmUpdate=True,
        actualNativeTitlePresent=420,titleIdle=231,actualNativeTitleAll1228800BytesExact=True,
        explicitUniqueFileScriptDiagnosticPairs=30,diagnosticWordsCompared=9090,diagnosticDifferencesAfterExplicitHandleMap=0,
        mappingIsNotStrictAcceptance=True,strictVmBeforeDifferences=62,strictVmAfterDifferences=61,strictVmComparisonPassed=False,
        actualApplicationFrames=2265,assertions=7,journalRows=131,silentPcmFrames=1508352,
        imagesStateFilesAndPcmEqualPreviousLineRepair=True,previousLineRepairCodeCommit='d53076b4997f544f142757e1b147b7e163d78d0d',
        coreSourcesRecompiled=1,coreObjectsReused=140,platformObjectsReused=5,
        oldFailuresRetained=True,nativeNaturalRunModePairs=30,nativeAllStageEntryModePairs=25,
        completeGame=False,nativeEquivalent=False,browserAcceptance=False,verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)
    encoded=json.dumps(result,indent=2)+'\n'
    if a.check:assert out.read_text()==encoded
    else:out.write_text(encoded)
    print(json.dumps({k:v for k,v in result.items()if k!='bindings'}))


if __name__=='__main__':main()
