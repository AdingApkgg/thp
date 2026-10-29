"""Review source/build bindings and finite VM-return regression evidence."""
from pathlib import Path
import argparse, hashlib, importlib.util, json

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def review():
    home=ROOT/'artifacts/th14/vm-return-worker-oct29';bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def load(path):return json.loads(read(path))
    browser=load(home/'browser-candidate/build.json');core=load(home/'native-core/observer-build.json')
    assert browser['compiledUnits']==146 and browser['reusedObjectCount']==0
    assert browser['rootUnrelatedResourceCryptExcluded'] and len(core['objectBindings'])==141
    source={}
    for name in ['AnmManager.cpp','AnmManager.hpp','GameBattle.cpp']:
        key='th12_web/cpp/game/'+name;raw=read(ROOT/'runtimes/th12'/key)
        assert SHA(raw)==browser['sourceBindings'][key]['sha256']
        assert raw==read(home/'browser-candidate/source'/key)
        source[key]=SHA(raw)
    assert SHA(read(ROOT/'tools/th14-build-webgpu-release.py'))==browser['toolSha256']
    assert SHA(read(home/'browser-candidate/th14-sdl.wasm'))==browser['wasmSha256']
    observer=load(home/'observer-v2/observer-build.json')
    assert SHA(read(home/'observer-v2/observer.wasm'))==observer['wasmSha256']
    for row in core['objectBindings']:assert SHA(read(Path(row['path'])))==row['sha256']
    control=load(home/'controlled-after-vm-verified.json')
    spec=importlib.util.spec_from_file_location('vm_evidence',ROOT/'tools/th14-controlled-vm-worker-evidence-oct29.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert module.evidence(ROOT/'artifacts/th14/sht-worker-oct29/controlled-after-vm-native')==control
    camera=load(home/'controlled-prefix33000/camera-report.json')
    assert not camera['allCameraWordsEqual']and camera['counts']=={'12':17039}
    candidate=load(home/'controlled-prefix33000/report.json');old=load(home/'old-controlled-prefix33000/report.json')
    assert candidate['allRaw32ByteIdentical']and old['allRaw32ByteIdentical']
    assert candidate['normalVmBoundaryObservation']['modelClock']['delivered']==1
    assert old['normalVmBoundaryObservation']['modelClock']['delivered']==0
    assert old['normalVmReturnBoundaryUnsupported']
    regression=load(ROOT/'artifacts/th14/scene-publish-window-oct30/passive-regression-verified.json')
    assert regression['verifiedFiniteEvidence']and regression['callbacks']==33000 and regression['vm303Rows']==629 and regression['combatCheckpoints']==304
    assert regression['verifierSha256']==SHA(read(ROOT/'tools/th14-verify-native-campaign.py'))
    locations=[home/'native-gles-baseline-v3',home/'native-webgpu-baseline-v2',ROOT/'artifacts/th14/mode-coverage-oct29/normal-pump-native-webgpu-baseline']
    runs=[load(path/'report.json')for path in locations]
    assert all(r['completed']and r['frames']==2264 and not r['error']for r in runs)
    for key in ['rows','actions','checks','captures','initialSave','finalSave','files','pcmFrames','pcmSha256','finalReferenceState','initialLoadingObservations']:
        assert runs[0][key]==runs[1][key]==runs[2][key]
    for capture in runs[0]['captures']:
        images=[read(path/capture['file'])for path in locations]
        assert images[0]==images[1]==images[2]and SHA(images[0])==capture['sha256']
    browser_state=load(home/'work-state.json')
    assert browser_state['browserStage5To6Observed']and browser_state['browserStage6BossObserved']and not browser_state['browserFullReplayFinished']
    return dict(verifiedFiniteVmReturnReview=True,sourceBindings=source,browserCompiledUnits=146,nativeCoreUnits=141,
        browserMainWasmSha256=browser['wasmSha256'],observerWasmSha256=observer['wasmSha256'],
        controlledOriginalReturnPc='0x47e660',controlledCallbacks=33000,controlledOwnSuspendIncrementPerThread=1,
        candidateVmReturnClockDelivered=True,retainedOldCoreCannotDeliverVmReturnClock=True,
        controlledStrictCameraPassed=False,controlledCameraMismatchRows=17039,oldIndependentFailureClosed=False,
        independentRegressionCallbacks=33000,independentRegressionVmRows=629,independentRegressionCombatCheckpoints=304,
        nativeApplicationFramesPerBackend=2264,nativeAssertionsPerBackend=7,nativePcmFramesPerBackend=1508352,
        nativeImagesStateFilesAndPcmUnchanged=True,nativeApplicationWorkerFeatureOff=True,
        browserStage5To6AndBossObserved=True,browserNaturalEndAndPersistenceAccepted=False,
        nativeNaturalRunModePairs=30,nativeAllStageEntryModePairs=25,
        ordinaryIndependentThreadTimingAccepted=False,completeGame=False,nativeEquivalent=False,
        verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'docs/porting')or out.is_relative_to(ROOT/'artifacts/th14')
    result=review()
    if a.check:assert json.loads(out.read_bytes())==result
    else:out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k not in ['bindings','sourceBindings']}))


if __name__=='__main__':main()
