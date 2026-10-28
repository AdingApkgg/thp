"""Recompute finite TH14 replay text and observed-availability evidence.

The strict positive cases declare original resource readiness as an external
component input. They cannot establish independent production scheduling.
"""
from pathlib import Path
import argparse,hashlib,importlib,json,struct,sys

ROOT=Path(__file__).resolve().parents[1]
HOME=ROOT/'artifacts/th14/native-frame-readback-oct28'
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def evidence():
    bindings={}
    def raw(path):
        path=path.resolve(strict=True);assert path.is_relative_to(ROOT)
        b=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
    def load(path):return json.loads(raw(path))
    component=load(HOME/'replay-fps-text-component-v3/report.json')
    assert component['passed']and component['cases']==8192 and component['queuedCases']==512
    assert all(x['passed']for x in component['rows'])
    assert component['toolSha256']==SHA(raw(ROOT/'tools/th14-replay-fps-text-oct28.py'))
    header=ROOT/'runtimes/th12/th12_web/cpp/game/ReplayTextTh14.hpp'
    assert component['productionHeaderSha256']==SHA(raw(header))
    sys.path.insert(0,str(ROOT/'tools'));image,*_=importlib.import_module('th-anm-handlers').handlers(14)
    assert SHA(image.data)==component['nativeExecutableSha256']
    assert image.read(0x454b13,2)==bytes.fromhex('6a3e')
    assert image.read(0x455eb9,7)==bytes.fromhex('f6808000000004')
    native_home=HOME/'inline-ecl-worker-boundaries-v2';n=load(native_home/'report.json')
    assert n['childExited']and n['frameReadbackCompleted']and not n['error']
    assert n['sourceSha256']==SHA(raw(native_home/'run-tool.py'))==SHA(raw(ROOT/'tools/th14-native-device-observer-oct27.py'))
    assert n['originalCodeWrites']==n['gameStateWrites']==0 and not n['inputInjection']
    assert n['threadContextRedirects']==2 and n['readback']['cleanupResults']==[0,0,1]
    assert n['inlineEclAnmBoundariesComplete']and n['stageWorkerBoundariesComplete']
    inline=n['inlineEclAnmBoundaries'];assert len(inline)==6
    for index in (0,3):
        a,b,c=inline[index:index+3]
        assert [x['phase']for x in (a,b,c)]==['cpu-entry','gpu-published','gpu-wait-exit']
        assert a['file']==b['file']==c['file']and b['cursor128']==1 and c['cursor128']==0
    assert inline[3]['hostMonotonicNs']>=inline[2]['hostMonotonicNs']
    native_pixels=raw(native_home/n['readback']['file']);assert SHA(native_pixels)==n['readback']['pixelSha256']and len(native_pixels)==1228800
    original_vm=load(native_home/'live-vms-before-readback.json')
    native_ages=[x['ageCurrent']for x in original_vm['rows']if x['file']==9 and x['script']==10]
    assert len(native_ages)==4 and len(set(native_ages))==1
    failures={}
    for name,vm_count,pixels,byte_count in [('inline-ecl-baseline-strict.json',20,1129,3854),
        ('inline-ecl-availability-strict.json',0,165,658),('replay-fps-gles-baseline-strict.json',20,964,3196)]:
        d=load(HOME/name);assert not d['strictAllSelectedStateLiveVmsAndPixelsEqual']
        assert len(d['strictVmDifferences'])==vm_count and d['pixelDifferentPixels']==pixels and d['pixelDifferentBytes']==byte_count
        assert d['bothRngEqual']and d['strictRegistryOrderEqual']and not d['strictExtraPortHandles']
        failures[name]=dict(strictVmDifferenceWords=vm_count,pixelDifferentPixels=pixels,pixelDifferentBytes=byte_count)
    positives=[]
    core=load(HOME/'replay-fps-core-v2/observer-build.json')
    session_path='runtimes/th12/th12_web/cpp/game/GameSession.cpp';session_sha=SHA(raw(ROOT/session_path))
    assert core['sourceHashes']['th12_web/cpp/game/GameSession.cpp']==session_sha
    assert core['headerHashes']['th12_web/cpp/game/ReplayTextTh14.hpp']==component['productionHeaderSha256']
    for backend in ('gles','webgpu'):
        control=HOME/f'replay-fps-{backend}-availability-v2';port=control/'run'
        d=load(HOME/f'replay-fps-{backend}-availability-v2-strict.json')
        assert d['strictAllSelectedStateLiveVmsAndPixelsEqual']and d['noPixelToleranceOrFpsNormalization']
        assert d['nativeLiveVms']==d['portLiveVms']==334 and d['wordsPerVm']==303
        assert d['bothRngEqual']and d['selectedFieldsEqual']and d['strictRegistryOrderEqual']
        assert not d['strictVmDifferences']and not d['strictExtraPortHandles']
        assert d['pixelDifferentBytes']==d['pixelDifferentPixels']==0
        for path,digest in d['bindings'].items():
            b=raw(ROOT/path);assert len(b)==digest['bytes']and SHA(b)==digest['sha256'],path
        run=load(port/'report.json');assert run['completed']and not run['error']and run['checks']and all(x['passed']for x in run['checks'])
        assert run['toolSha256']==SHA(raw(port/'run-tool.py'))
        profile=load(control/'availability.json')
        assert profile['nativeReport']['sha256']==SHA(raw(native_home/'report.json'))
        assert profile['sourceToolSha256']==SHA(raw(ROOT/'tools/th14-native-availability-control-oct28.py'))
        availability=run['observedResourceAvailabilityControl']
        assert availability['profile']==profile and availability['gameStateAndRngNeverReplaced']and not availability['productionSchedulingChanged']
        assert len(availability['events'])==len(profile['deliveries'])
        first={};origin=profile['originalPlayerConstructionPresent']
        for row in n['mainResourcePumpEntries']:
            for slot in row['slots']:
                if slot['file']!=9 and slot['words128Through134'][0]and row['precedingPresentEntries']>=origin:
                    first.setdefault(slot['file'],row['precedingPresentEntries'])
        assert profile['deliveries']==[dict(resourceFile=f,mainPumpOffsetFromPlayer=p-origin)for f,p in first.items()]
        build=load(HOME/f'replay-fps-{backend}-build-v2/build.json')
        assert build['coreSourceHashes']['th12_web/cpp/game/GameSession.cpp']==session_sha
        assert build['sourceBindings']['runtimes/th12/th12_web/cpp/game/ReplayTextTh14.hpp']['sha256']==component['productionHeaderSha256']
        assert run['wasmSha256']==build['wasmSha256']
        capture=run['captures'][0];pixels=raw(port/capture['file']);assert pixels==native_pixels
        vm=load(port/capture['liveAnimations']['file'])
        ages=[x[7]for x in vm['rows']if x[1]==9 and x[2]==10];assert ages==native_ages
        positives.append(dict(backend=backend,applicationFrames=run['frames'],checks=len(run['checks']),
            liveVms=334,wordsPerVm=303,rawHandlesAndRegistryOrderExact=True,bothRngExact=True,
            bgraBytesCompared=len(pixels),differentBytes=0,wasmSha256=run['wasmSha256'],
            externalResourceReadinessDeclared=True,productionSchedulingAccepted=False))
    candidate=load(HOME/'replay-fps-browser-candidate-v2/build.json')
    assert candidate['compiled']and candidate['compiledUnits']==candidate['sourceUnits']==146 and candidate['reusedObjectCount']==0
    assert candidate['sourceBindings']['th12_web/cpp/game/GameSession.cpp']['sha256']==session_sha
    assert candidate['sourceBindings']['th12_web/cpp/game/ReplayTextTh14.hpp']['sha256']==component['productionHeaderSha256']
    assert candidate['rootUnrelatedResourceCryptExcluded']and not candidate['retailAssetsIncluded']
    transport=load(HOME/'replay-fps-launcher-v2/http-check.json')
    served=load(HOME/'replay-fps-launcher-v2/served-current.json')
    assert transport['verifiedTransport']and transport['routes']==139 and len(transport['requests'])==27
    assert transport['wasmSha256']==served['wasmSha256']==candidate['wasmSha256']
    assert served['actualServedMainAndWorkerBytesEqual']and served['quietInjectedIntoParentAndIframe']
    for name in ('automatic-demo-recorded-fps','saved-replay-list','ordinary-replay-recorded-fps','ordinary-replay-natural-end'):
        picture=raw(HOME/f'replay-fps-browser-ui-v2/{name}.jpg');assert picture[:3]==b'\xff\xd8\xff'
        ax=raw(HOME/f'replay-fps-browser-ui-v2/{name}.ax.txt').decode()
        assert 'runtimeEpoch=1'in ax and '音频 0ms'in ax and '本机测试静音'in ax
    console=load(HOME/'replay-fps-browser-ui-v2/console.json')
    assert any('[replay] selected: record stage 1, character 0 subtype 0 difficulty 1, 823 bytes'in x['message']for x in console)
    return dict(verifiedFiniteReplayFpsFix=True,productionReplayFpsTextAdded=True,retailRequestCases=8192,
        retailDrawPriority=62,retailControllerLoadingFlag=4,retailDrawWrapperAndBodyCovered=True,
        recordedRateByteValues=256,positiveComponentCases=positives,retainedNegativeControls=failures,
        nativePresent=2278,nativeStage=3,nativeControllerFrame=241,nativeOptionAges=native_ages,
        observedInlineEclAnm=[dict(file=x['file'],phase=x['phase'],precedingPresentEntries=x['precedingPresentEntries'])for x in inline],
        browserCandidateCompiledUnits=146,browserCandidateWasmBytes=candidate['wasmBytes'],browserCandidateWasmSha256=candidate['wasmSha256'],
        browserTransportRoutes=139,browserHttpRequests=27,actualBrowserRecordedFpsVisuallyObserved=True,
        actualBrowserAutomaticDemoAndOrdinaryReplayObserved=True,actualBrowserPartialReplayNaturalEndObserved=True,
        browserVisualObservationIsNotStrictPixelComparison=True,
        nativeChildExited=True,originalCodeWrites=0,originalGameStateWrites=0,nativeReadbackContextRedirects=2,
        originalHardwareObservationPerturbsScheduling=True,originalResourceReadinessIsDeclaredComponentInput=True,
        fixedFrameOrVmAgePatchInProduction=False,independentProductionSchedulingAccepted=False,
        firstOriginalGameFrameStrictDifferenceClosed=False,completeBrowserAcceptance=False,
        physicalAudioDevicesOpened=0,completeGame=False,nativeEquivalent=False,
        verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    proof=evidence();target=ROOT/'docs/porting/th14-replay-fps-verified-oct28.json'
    if a.check:assert json.loads(target.read_bytes())==proof
    else:target.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:proof[k]for k in ('verifiedFiniteReplayFpsFix','retailRequestCases','nativeStage','nativeControllerFrame','browserCandidateCompiledUnits','completeGame','independentProductionSchedulingAccepted')}))


if __name__=='__main__':main()
