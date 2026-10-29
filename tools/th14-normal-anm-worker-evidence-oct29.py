"""Recompute the bounded normal-ANM loader and worker-clock increment evidence."""
from pathlib import Path
import argparse,hashlib,json,re
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/mode-coverage-oct29';OLD=R/'artifacts/th14/native-frame-readback-oct28'
SHA=lambda raw:hashlib.sha256(raw).hexdigest()

def evidence():
    bindings={}
    def raw(path):
        path=path.resolve(strict=True);assert path.is_relative_to(R);data=path.read_bytes()
        bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
    def load(path):return json.loads(raw(path))
    def check(path,digest):assert SHA(raw(path))==digest,str(path)
    current_tool=SHA(raw(R/'tools/th14-verify-native-campaign.py'))
    controlled=load(H/'normal-pump-controlled-entry-public-prefix33000-verified.json')
    assumed=load(H/'normal-pump-proposed-full80324-verified.json')
    original_control=load(H/'controlled-normal-entry-verified.json')
    assert controlled['verifierSha256']==assumed['verifierSha256']==current_tool
    assert controlled['callbacks']==33000 and controlled['vm303Rows']==653 and controlled['combatCheckpoints']==288
    assert controlled['orderedPublications']==2870 and controlled['diagnosticPrefixOnly']and not controlled['ordinaryIndependentThreadTimingAcceptance']
    assert controlled['controlledThreadObservationSha256']==SHA(raw(H/'controlled-normal-entry-verified.json'))
    assert original_control['verifiedControlledOriginalNormalAnmBoundary']and original_control['originalMainHoldPc']==0x47e5e0
    assert original_control['holdNanoseconds']==70609500 and not original_control['ordinaryIndependentThreadTimingAcceptance']
    assert original_control['verifierSha256']==SHA(raw(R/'tools/th14-controlled-worker-boundary-evidence-oct29.py'))
    assert assumed['callbacks']==80324 and assumed['vm303Rows']==866 and assumed['combatCheckpoints']==636
    assert assumed['proposedNormalBoundaryAssumption']and not assumed['exactOriginalInstructionBoundaryAccepted']and not assumed['ordinaryIndependentThreadTimingAcceptance']
    assert assumed['originalNaturalReplayEndObserved']and assumed['stagesObserved']==[1,2,3,4,5]
    for proof in [controlled,assumed,original_control]:
        assert not proof['completeGame']and not proof['nativeEquivalent']
        for name,row in proof['bindings'].items():check(R/name,row['sha256'])
    for proof in [controlled,assumed]:
        for key in ['allSelected32Equal','allCamera25Equal','allHud2Equal','allVm303AndRegistryOrderEqual','allCapturedCombatWordsEqual']:assert proof[key],key
    old_control=load(H/'old-pump-controlled-entry-prefix33000/report.json');assert old_control['allRaw32ByteIdentical']and not old_control['firstDifference']
    wrong=load(H/'normal-pump-controlled-prefix33000/report.json')
    assert wrong['firstDifference']==dict(index=31016,stage=3,stageFrame=0,word=21,native=5435,portable=56097)
    old_gap=load(H/'marisaa-easy-toho-prefix48000-warm-flag/report.json')
    assert old_gap['firstDifference']==dict(index=30990,stage=3,stageFrame=0,word=21,native=56097,portable=5435)
    guards=load(H/'normal-boundary-scope-guards/check.json');assert guards['passed']and len(guards['cases'])==3 and all(row['rejected']for row in guards['cases'])
    for name,digest in guards['sourceBindings'].items():check(R/name,digest)
    for row in guards['cases']:check(H/'normal-boundary-scope-guards'/(row['name']+'.log'),row['logSha256'])
    unit=load(H/'stage-worker-clock-unit-build-v2/build.json');tests=load(H/'stage-worker-clock-unit-check-v2/check.json')
    assert unit['compiled']and tests['passed']and tests['actualProductionWaitHelper']and len(tests['checks'])==10
    assert unit['wasmSha256']==tests['wasmSha256'];check(H/'stage-worker-clock-unit-build-v2/wait.wasm',unit['wasmSha256'])
    for name,digest in unit['sourceBindings'].items():check(R/name,digest)
    check(R/'tools/th14-stage-worker-wait-build-oct29.py',unit['toolSha256']);check(R/'tools/th14-stage-worker-wait-check-oct29.mjs',tests['checkerSha256'])
    build=load(H/'normal-pump-browser-candidate-v2/build.json');before=load(OLD/'later-stage-browser-candidate/build.json')
    changed={'th12_web/cpp/game/GameBattle.cpp','th12_web/cpp/game/GameBattle.hpp','th12_web/cpp/game/GameSession.cpp','th12_web/cpp/sdl/Application.cpp','th12_web/cpp/sdl/StageWorkerWaitTh14.hpp'}
    assert build['basePublishedCommit']=='2a21402eb504627707b39c091eeee191cf84c21f'and build['compiledUnits']==146 and build['reusedObjectCount']==0
    assert {name for name,row in build['sourceBindings'].items()if name not in before['sourceBindings']or row['sha256']!=before['sourceBindings'][name]['sha256']}==changed
    for name,row in build['sourceBindings'].items():check(H/'normal-pump-browser-candidate-v2/source'/name,row['sha256'])
    for name in changed:check(R/'runtimes/th12'/name,build['sourceBindings'][name]['sha256'])
    assert build['rootUnrelatedResourceCryptExcluded']and not build['retailAssetsIncluded']and build['archiveWorkerFiles']==before['archiveWorkerFiles']
    check(R/'tools/th14-build-webgpu-release.py',build['toolSha256']);check(H/'normal-pump-browser-candidate-v2/th14-sdl.wasm',build['wasmSha256'])
    check(H/'normal-pump-browser-candidate-v2/th14-sdl.mjs',build['loaderSha256'])
    for name,row in build['archiveWorkerFiles'].items():check(H/'normal-pump-browser-candidate-v2'/name,row['sha256'])
    observer=load(H/'normal-pump-public-observer/observer-build.json')
    assert observer['wasmSha256']==controlled['wasmSha256']==assumed['wasmSha256']and not observer['vmCallbackPointersWrapped']
    assert observer['engineSourcesRecompiledForThisLink']==0 and observer['engineObjectsReusedForThisLink']==141
    check(R/'tools/th14-normal-worker-observer-build-oct29.py',observer['buildToolSha256']);check(H/'normal-pump-public-observer/observer.wasm',observer['wasmSha256'])
    for name,digest in observer['fixtureDependencyHashes'].items():check(Path(name),digest)
    for row in observer['objectBindings']:check(Path(row['path']),row['sha256'])
    pair=load(H/'normal-pump-native-pair.json');assert pair['passed']and pair['backendsAndPreviousEqual']and pair['physicalAudioDevicesOpened']==0
    homes=[H/'normal-pump-native-gles-baseline',H/'normal-pump-native-webgpu-baseline',OLD/'later-stage-native-gles-baseline']
    runs=[load(home/'report.json')for home in homes]
    for run in runs:assert run['completed']and not run['error']and run['frames']==run['applicationTicks']==2264 and len(run['checks'])==7 and run['physicalAudioDevicesOpened']==0
    for key in pair['fields']:assert runs[0][key]==runs[1][key]==runs[2][key],key
    for capture in runs[0]['captures']:
        assert raw(homes[0]/capture['file'])==raw(homes[1]/capture['file'])==raw(homes[2]/capture['file'])
        for home in homes:check(home/capture['file'],capture['sha256']);check(home/capture['liveAnimations']['file'],capture['liveAnimations']['sha256'])
    for backend,run in zip(['gles','webgpu'],runs[:2]):
        native=load(H/f'normal-pump-native-{backend}-build/build.json');assert native['wasmSha256']==run['wasmSha256']
        check(H/f'normal-pump-native-{backend}-build/application.wasm',native['wasmSha256'])
        for name,row in native['sourceBindings'].items():check(R/name,row['sha256'])
    flow=load(H/'normal-pump-browser-ui/flow-receipt.json')
    assert flow['stage5ReplayStarted']and flow['stage5To6TransitionObserved']and flow['stage6RunningObserved']
    assert flow['runtimeEpoch']==3 and flow['mainWasmSha256']==build['wasmSha256']and flow['quiet']
    assert not flow['ordinaryRunComparedToRetail']and not flow['completeGame']and not flow['nativeEquivalent']
    ui=H/'normal-pump-browser-ui';replay=raw(ui/'input/th14_ud0000.rpy')
    assert len(replay)==110306 and SHA(replay)==flow['replaySha256']=='866bf6bac02e1c2b9067dacce6705dc71a512eeb2755106474be492a2d23dcdc'
    for name in flow['evidenceFiles']:raw(ui/name)
    messages=[row['message']for row in load(ui/'stage6-running-logs.json')]
    assert any('[replay] selected: record stage 5, character 2 subtype 1 difficulty 2, 110306 bytes'in message for message in messages)
    waits=[float(re.search(r'after ([0-9.]+)ms',message).group(1))for message in messages if '[loading14] worker wait completed after'in message]
    assert len(waits)==1 and waits[0]>=60
    served=load(H/'normal-pump-launcher/served-current.json');assert served['actualServedMainAndWorkerBytesEqual']and served['quietInjectedIntoParentAndIframe']and served['wasmSha256']==build['wasmSha256']
    return dict(verifiedFiniteNormalAnmWorkerPoll=True,productionFiles=sorted(changed),workerMinimumWaitChecks=10,
        controlledPrefixCallbacks=33000,controlledVmRows=653,controlledCombatCheckpoints=288,controlledInitialPublications=2870,
        controlledOldLoaderAlsoPasses=True,controlledExactNormalEntryPc=0x47e5e0,controlledHoldNanoseconds=70609500,
        proposedBoundaryCallbacks=80324,proposedVmRows=866,proposedCombatCheckpoints=636,proposedExactOriginalInstructionPlacementAccepted=False,
        vmCallbackPointersWrapped=False,originalRngCounterOrAddressValuesProvided=False,scopeGuardsRejected=3,
        originalLongerPrefixFailureRetained=True,mistakenDraw35BoundaryNegativeRetained=True,
        nativeApplicationFramesPerBackend=2264,nativeAssertionsPerBackend=7,nativeImagesAndVmAndFileStateEqual=True,nativePcmFramesPerBackend=1508352,
        nativeApplicationArchiveWorkerFeatureOff=True,browserCompiledUnits=146,browserMainWasmSha256=build['wasmSha256'],browserStage5To6Observed=True,
        browserRuntimeEpoch=3,browserQuiet=True,browserWholeReplayFromStage1Accepted=False,
        ordinaryIndependentThreadTimingAcceptance=False,nativeNaturalRunModePairs=30,nativeAllStageEntryModePairs=25,
        bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()),
        limitations=['The original33,000-callback case uses declared main-thread scheduling; the old loader also passes this case.','The old80,324-callback result needs a proposed clock-delivery boundary and naturally ends in stage5; it is not an independent original instruction-placement proof or all-stage clear.','The real browser observation starts in stage5 and covers its transition to6; no whole-run pixels/PCM, continuous60FPS or ordinary original cold Replay acceptance.','All-mode completion and whole-game1:1 remain unaccepted.'],completeGame=False,nativeEquivalent=False)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    output=R/'docs/porting/th14-normal-anm-worker-verified-oct29.json';result=evidence()
    if args.check:assert json.loads(output.read_bytes())==result
    else:output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({key:result[key]for key in ['verifiedFiniteNormalAnmWorkerPoll','controlledPrefixCallbacks','proposedBoundaryCallbacks','browserStage5To6Observed','ordinaryIndependentThreadTimingAcceptance']}))
if __name__=='__main__':main()
