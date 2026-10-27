"""Bind two actual native gameplay frames, including their required failures."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,struct

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--home',type=Path,default=ROOT/'artifacts/th14/native-frame-readback-oct27')
    p.add_argument('--output',type=Path,default=ROOT/'docs/porting/th14-first-native-demo-verified-oct27.json')
    p.add_argument('--check',action='store_true');a=p.parse_args();home=a.home.resolve();out=a.output.resolve()
    assert home.is_relative_to(ROOT/'artifacts/th14')and out.is_relative_to(ROOT);bindings={}
    def read(path):
        path=path.resolve();assert path.is_relative_to(ROOT);raw=path.read_bytes()
        bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def load(path):return json.loads(read(path))
    observer=read(ROOT/'tools/th14-native-device-observer-oct27.py')
    comparator=read(ROOT/'tools/th14-native-game-frame-compare-oct27.py')
    helper=ROOT/'tools/th14-native-title-live-compare-oct27.py';read(helper)
    spec=importlib.util.spec_from_file_location('native_demo_words',helper);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    build=load(home/'deadline-observer-webgpu-build-v2/build.json')
    assert SHA(read(home/'deadline-observer-webgpu-build-v2/application.wasm'))==build['wasmSha256']
    for path,row in build['sourceBindings'].items():assert SHA(read(ROOT/path))==row['sha256'],path
    for row in build['coreObjects']:assert SHA(read(Path(row['path'])))==row['sha256']
    cases=[]
    for native_name,port_name,result_name,ordinal,byte_count,pixel_count,age_delta in [
        ('first-native-demo-frame','first-demo-from-native-webgpu-v2','first-native-demo-strict-public.json',2277,3883,1147,5),
        ('first-demo-native-public-pump','first-demo-public-webgpu','first-demo-public-strict.json',2276,3854,1129,6)]:
        n=home/native_name;q=home/port_name;nr=load(n/'report.json');pr=load(q/'report.json');result=load(home/result_name)
        assert nr['childExited']and nr['frameReadbackCompleted']and not nr['error']and pr['completed']and not pr['error']
        assert nr['sourceSha256']==SHA(read(n/'run-tool.py'))and pr['toolSha256']==SHA(read(q/'run-tool.py'))
        if native_name=='first-demo-native-public-pump':assert nr['sourceSha256']==SHA(observer)and nr['plan']['captureStageTriggerObserved']
        assert nr['readback']['statusesAtCaptureStop'][:5]==[0]*5 and nr['readback']['cleanupResults']==[0,0,1]
        assert nr['threadContextRedirects']==2 and nr['originalCodeWrites']==nr['gameStateWrites']==0 and not nr['inputInjection']
        s=next(x for x in nr['rows']if x['kind']=='native-Present-entry'and x['ordinal']==ordinal)
        assert s['stage']==3 and s['stageFrame']==241 and s['gameFlags']==0x40
        assert pr['wasmSha256']==build['wasmSha256']and pr['frames']==2264 and len(pr['checks'])==7
        assert pr['physicalAudioDevicesOpened']==0 and len(pr['captures'])==1
        c=pr['captures'][0];rng=struct.unpack('<HHIHHI',bytes.fromhex(s['rngHex']))
        assert c['referenceState'][:7]==[s['originalInitialTicks'],s['originalProcessCookie'],0,rng[0],rng[2],rng[3],rng[5]]
        assert rng[2]==8640 and rng[5]==114
        native=read(n/nr['readback']['file']);port=read(q/c['file']);assert len(native)==len(port)==1228800
        assert SHA(native)==nr['readback']['pixelSha256']and SHA(port)==c['sha256']
        difference=[i for i,(x,y)in enumerate(zip(native,port))if x!=y];pixels={i//4 for i in difference}
        assert len(difference)==byte_count and len(pixels)==pixel_count
        assert result['sourceSha256']==SHA(comparator)and not result['strictAllSelectedStateLiveVmsAndPixelsEqual']
        assert result['externalStartupInputsAndBothRngEqual']and result['selectedFieldsEqual']
        assert result['pixelDifferentBytes']==byte_count and result['pixelDifferentPixels']==pixel_count
        nv=load(n/'live-vms-before-readback.json');pv=load(q/c['liveAnimations']['file'])
        assert len(nv['rows'])==len(pv['rows'])==pv['expected']==339 and pv['comparedValues']==303
        address={struct.unpack_from('<I',bytes.fromhex(x['rawVmHex']),0x570)[0]:x['handle']for x in nv['rows']}
        ns={x['handle']>>13:x for x in nv['rows']};ps={x[0]>>13:x for x in pv['rows']};assert set(ns)==set(ps)and len(ns)==339
        remap={x['handle']:ps[k][0]for k,x in ns.items()};mapped=sum(x!=y for x,y in remap.items())
        links={'handle','parentHandle','registryNextHandle','registryPreviousHandle','childNextHandle','childPreviousHandle'}
        diagnostic=[]
        for serial,row in ns.items():
            fields,words=m.native_words(row,address)
            for field,x,y in zip(fields,words,ps[serial]):
                if field in links:x=remap.get(x,x)
                if x!=y:diagnostic.append((serial,row['file'],row['script'],field,x,y))
        assert len(diagnostic)==20 and {x[0]for x in diagnostic}=={85,86,87,88}
        assert all(x[1:3]==(9,10)for x in diagnostic)
        assert {x[3]for x in diagnostic}=={'ageCurrent','nativeVmWord0x55c','nativeVmWord0x560','nativeVmWord0x564','nativeVmWord0x50'}
        assert all(x[4]-x[5]==age_delta for x in diagnostic if x[3]=='ageCurrent')
        assert len(result['exploratoryAfterHandleMappingDifferences'])==20
        if age_delta==6:
            assert mapped==0 and result['strictRegistryOrderEqual']and len(result['strictVmDifferences'])==20 and not result['strictExtraPortHandles']
            assert len(nr['mainResourcePumpEntries'])==287
        else:assert mapped==41 and not result['strictRegistryOrderEqual']
        cases.append(dict(nativePresent=ordinal,stage=3,controllerAndBattleFrame=241,cppApplicationFrames=2264,
            liveVms=339,wordsPerVm=303,bothRngSeedsAndCountsEqual=True,selectedEconomyAndModeEqual=True,
            differentPixelBytes=byte_count,differentPixels=pixel_count,strictFramePassed=False,
            rawHandlesAndRegistryOrderAllEqual=mapped==0,explicitlyMappedHandlesInSeparateDiagnostic=mapped,
            exploratoryRemainingWords=20,optionAnimationAgeDelta=age_delta,mappingIsNotStrictAcceptance=True))
    probe=load(home/'initial-upload-observed/report.json')
    assert probe['completed']and probe['privateReadOnlyLoadingProbe']and probe['frames']==2024
    assert probe['toolSha256']==SHA(read(home/'initial-upload-observed/run-tool.py'))
    probe_build=load(home/'initial-upload-observer-build/build.json')
    assert probe['buildReportSha256']==SHA(read(home/'initial-upload-observer-build/build.json'))
    assert probe['wasmSha256']==probe_build['wasmSha256']==SHA(read(home/'initial-upload-observer-build/application.wasm'))
    assert probe_build['coreObjects']==build['coreObjects']and probe_build['reusedPlatformObjects']==build['reusedPlatformObjects']
    for path,row in probe_build['sourceBindings'].items():assert SHA(read(ROOT/path))==row['sha256'],path
    for path,digest in probe_build['newObjects'].items():assert SHA(read(home/'initial-upload-observer-build'/path))==digest
    fixture=read(home/'initial-upload-observer-build/fixture.cpp').decode().replace('\r\n','\n')
    public=read(ROOT/'runtimes/th12/th12_web/tests/cpp/th14-native-title-fixture.cpp').decode().replace('\r\n','\n')
    assert fixture.startswith(public)and 'component_loading_state()'in fixture and 'std::fflush(stdout)'in fixture
    counts={row['words'][9]:row['words'][11]for row in probe['initialLoadingObservations']if row['words'][9]!=0xffffffff}
    assert counts=={9:13,4:5,6:2,10:3,11:16}
    assert probe['initialLoadingObservations'][0]['words'][12]==0
    assert next(row['frame']for row in probe['initialLoadingObservations']if row['words'][12])==1998
    budget_failure=load(home/'first-demo-from-native-webgpu/report.json')
    assert not budget_failure['completed']and '4096'in budget_failure['error']and budget_failure['frames']==2237
    result=dict(schema='th14/first-actual-native-demo-finite-evidence/1',verifiedRetainedGameplayComparisons=True,
        cases=cases,rawOriginalGameFramesCaptured=True,referenceIsActualGameNotIndependentApiReplay=True,
        fourOptionAnimationsDifferDuringLoading=True,loadingAgeDifferenceVariesAcrossNativeProcesses=True,
        noFixedAgePatchOrStateReplacementUsed=True,readOnlyCppLoadingProbeFrames=2024,
        observedCppUploadCounts=counts,originalPumpCounterIsOneBased=True,extraFinalizationPassAssumptionRejected=True,
        initialCreationRingBudgetFailureRetained=True,creationObservationBudgetRaised=False,
        independentCpuClipPrototypeNotIntegrated=True,allOriginalChildrenExited=True,
        nativeReadbackPrivateCodeAndTwoContextRedirectsDeclared=True,
        originalGameCodeFieldsRngAndInputUnwritten=True,physicalUiAndAudioAccepted=False,
        completeGame=False,nativeEquivalent=False,browserAcceptance=False,nativeNaturalRunModePairs=30,nativeAllStageEntryModePairs=25,
        verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)
    encoded=json.dumps(result,indent=2)+'\n'
    if a.check:assert out.read_text()==encoded
    else:out.write_text(encoded)
    print(json.dumps({k:v for k,v in result.items()if k!='bindings'}))


if __name__=='__main__':main()
