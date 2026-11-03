"""Verify integrated resumable TH14 replay RNG stores without widening their scope."""
from pathlib import Path
import argparse, hashlib, json

R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/replay-rng-restore-nov04';C=H/'step-candidate'
sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true')
    parser.add_argument('--output',type=Path,default=R/'docs/porting/th14-replay-rng-step-nov04.json');args=parser.parse_args();bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=sha(raw));return raw
    def load(path):return json.loads(read(path))
    integrated=load(H/'integration.json');prepared=load(C/'prepared.json');core=load(C/'core/observer-build.json')
    assert integrated['integrated']and core['all141CoreObjectsRecompiled']and len(core['objectBindings'])==141
    assert sha(read(C/'core/observer.wasm'))==core['wasmSha256']==integrated['coreWasmSha256']
    for row in core['objectBindings']:assert sha(Path(row['path']).read_bytes())==row['sha256']
    for name,digest in {**core['sourceHashes'],**core['headerHashes']}.items():assert sha((Path(core['sourceSnapshotRoot'])/name).read_bytes())==digest
    for row in integrated['changedFiles']:assert sha(read(R/'runtimes/th12'/row['path']))==row['afterSha256']
    assert prepared['resumableNextStageRngThroughProductionLoader']and prepared['initialReplayConstructionStillSynchronous']
    assert prepared['preparerSha256']==sha(read(R/'tools/th14-prepare-replay-rng-step-loader-nov04.py'))
    assert prepared['parentPreparerSha256']==sha(read(R/'tools/th14-prepare-replay-rng-restore-nov04.py'))
    native=load(H/'native-component.json');unit=load(H/'step-component-verified-public.json')
    assert native['executedOriginalReplayRecordStoresAndMainRng']and native['instructionBytesUnmodified']
    assert native['cases']==len(native['profiles'])==15840 and len({tuple(row['input'])for row in native['profiles']})==15840
    assert native['syntheticInputsAndCpuSchedule']and native['optionalLockServicesDeclared']and not native['liveOriginalProcess']
    assert native['toolSha256']==sha(read(R/'tools/th14-replay-rng-restore-native-nov04.py'))
    assert unit['verifiedReplayAndRecordRngStoreOrder']and unit['cases']==unit['resumableJobCases']==unit['productionLoaderJobCases']==15840
    assert unit['modeCases']==[4320,5760,5760]and unit['traceSamples']==43200
    assert unit['candidateFinalDifferences']==unit['candidateTraceDifferences']==0
    assert unit['priorFinalDifferences']==[0,1440,1440]and unit['priorTraceDifferences']==[0,5760,5760]
    assert unit['readinessProtocolControls']==6 and unit['nativeProofSha256']==sha((H/'native-component.json').read_bytes())
    assert unit['toolSha256']==sha(read(R/'tools/th14-replay-rng-step-check-nov04.mjs'))
    assert unit['fixtureSha256']==sha(read(R/'runtimes/th12/th12_web/tests/cpp/th14-replay-rng-job-fixture-nov04.cpp'))
    read(R/'runtimes/th12/th12_web/tests/cpp/th14-replay-rng-restore-fixture-nov04.cpp')
    assert unit['headerSha256']==sha((R/'runtimes/th12/th12_web/cpp/game/ReplayRngRestoreTh14.hpp').read_bytes())
    for name,key in [('candidate.wasm','candidateWasmSha256'),('prior.wasm','priorWasmSha256')]:assert sha(read(H/'unit-step-public'/name))==unit[key]
    run=load(H/'step-session-public-run/step-session.json');failure=load(H/'step-session-failure-public-run/step-session-failure.json')
    session_build=load(H/'step-session-complete-build/observer-build.json')
    assert run['verifiedControlledProductionSessionRngResume']and run['actualGameSessionBattleAndStagedLoader']
    assert run['modeledCallbacks']==14303 and run['activeStage2Callbacks']==64 and not run['earlyHudSceneOrTimelineRequests']
    events=run['events'];assert len(events)==3 and [row[0]for row in events]==[0,2,3]
    assert [row[1]for row in events]==[14104,14106,14108]
    assert all(row[2]==row[3]==2 and row[9]==9 and row[10:]==[1,0]for row in events)
    assert events[0][4]==events[0][8]and events[1][6]==events[1][8]and events[2][5]==0
    script_draws=(events[2][7]-events[1][7])&0xffffffff;assert script_draws==24
    assert failure['verifiedControlledProductionSessionRngFailure']and failure['controlledFailureAt']==14106
    assert failure['completedSeedStores']==1 and failure['counterClearNotExecuted']and failure['errorPropagatedToGameSessionAndBattle']
    assert not failure['earlyHudSceneOrTimelineRequests']and not failure['originalCapturedScheduleEquivalenceAccepted']
    assert not run['nativeValuesProvidedToEngine']and not run['originalCapturedScheduleEquivalenceAccepted']
    assert run['wasmSha256']==failure['wasmSha256']==session_build['wasmSha256']==sha(read(H/'step-session-complete-build/observer.wasm'))
    for row in session_build['objectBindings']:assert sha(Path(row['path']).read_bytes())==row['sha256']
    assert session_build['objectBindings']==core['objectBindings']
    assert session_build['testFixtureSha256']==sha(read(R/'runtimes/th12/th12_web/tests/cpp/th14-replay-rng-step-session-fixture-nov04.cpp'))
    for path,digest in session_build['fixtureDependencyHashes'].items():assert sha(Path(path).read_bytes())==digest
    assert run['driverSha256']==sha(read(R/'tools/th14-replay-rng-step-session-check-nov04.mjs'))
    assert failure['driverSha256']==sha(read(R/'tools/th14-replay-rng-step-session-failure-check-nov04.mjs'))
    regressions=load(C/'regressions/end.json');assert regressions['finitePasses']==3 and regressions['callbacks']==199917
    modes=[]
    for row in regressions['results']:
        directory=C/'regressions'/row['key'];raw=load(directory/'raw-verified.json')
        assert row['strictAndIndependentPassed']and raw['verifiedFiniteEvidence']and raw['callbacks']==row['callbacks']
        assert raw['wasmSha256']==core['wasmSha256']and raw['verifierSha256']==sha(read(R/'tools/th14-verify-native-campaign.py'))
        for name in('exceptions','timing','scene'):assert load(directory/(name+'.json'))['passed']
        for path,binding in raw['bindings'].items():
            data=(R/path).read_bytes();assert len(data)==binding['bytes']and sha(data)==binding['sha256'],path
        modes.append(dict(key=row['key'],callbacks=raw['callbacks'],vmRows=raw['vm303Rows'],combatCheckpoints=raw['combatCheckpoints']))
    syntax=load(C/'syntax/report.json');assert syntax['passed']and len(syntax['cases'])==12
    for row in syntax['cases']:assert row['exitCode']==0 and row['sourceSha256']==sha((Path(core['sourceSnapshotRoot'])/'th12_web/cpp/game'/row['source']).read_bytes())
    app=load(H/'gles-two-stage/report.json');app_build=load(H/'gles-build/build.json')
    reference=load(R/'artifacts/th14/replay-cadence-reset-nov04/gles-two-stage/report.json')
    assert app['completed']and not app['error']and app['frames']==app['applicationTicks']==2289
    assert len(app['checks'])==27 and all(row['passed']for row in app['checks'])
    assert app['glCalls']['SDL_GL_SwapWindow']==2289 and app['physicalAudioDevicesOpened']==0
    assert app_build['coreWasmSha256']==core['wasmSha256']and app['wasmSha256']==app_build['wasmSha256']==sha(read(H/'gles-build/application.wasm'))
    assert app['toolSha256']==sha(read(R/'tools/th14-native-application-process-host-oct27.py'))
    assert app_build['toolSha256']==sha(read(R/'tools/th14-build-native-application.py'))
    assert app['captures']==reference['captures']and(app['pcmFrames'],app['pcmSha256'])==(reference['pcmFrames'],reference['pcmSha256'])
    for image in app['captures']:
        data=read(H/'gles-two-stage'/image['file']);assert sha(data)==image['sha256']and data==(R/'artifacts/th14/replay-cadence-reset-nov04/gles-two-stage'/image['file']).read_bytes()
    for path,binding in app_build['sourceBindings'].items():assert sha((R/path).read_bytes())==binding['sha256']
    browser=load(H/'browser-build/build.json');assert browser['compiled']and browser['sourceUnits']==browser['compiledUnits']==146
    assert not browser['browserRun']and not browser['browserAcceptance']
    assert browser['wasmSha256']==sha(read(H/'browser-build/th14-sdl.wasm'))and browser['loaderSha256']==sha(read(H/'browser-build/th14-sdl.mjs'))
    for name,digest in core['sourceHashes'].items():assert browser['sourceBindings'][name]['sha256']==digest,name
    for row in integrated['changedFiles']:assert browser['sourceBindings'][row['path']]['sha256']==row['afterSha256']
    read(R/'tools/th14-build-webgpu-reuse-worker-nov03.py')
    for path,digest in integrated['protectedFiles'].items():assert sha(read(R/path))==digest
    result=dict(verifiedIntegratedResumableReplayRngStores=True,nativeInstructionCases=15840,
        initialPlaybackCases=4320,nextStagePlaybackCases=5760,recordingCases=5760,
        cppDefaultRestoreCases=15840,resumableJobCases=15840,productionLoaderJobCases=15840,
        nativePostStoreSnapshots=43200,priorFinalRngDifferences=2880,candidateFinalRngDifferences=0,
        candidatePostStoreDifferences=0,readinessProtocolControls=6,
        controlledRealGameSessionCallbacks=14303,controlledStoreCallbacks=[14104,14106,14108],
        mainAnimationRngDrawsBetweenScriptStoreAndCounterClear=script_draws,
        controlledFailureCallback=14106,controlledFailureCompletedStores=1,
        earlyHudSceneOrTimelineRequests=False,all141CoreObjectsRecompiled=True,coreWasmSha256=core['wasmSha256'],
        finiteRegressions=modes,finiteCallbacks=199917,otherTitleSyntaxChecks=12,
        applicationFrames=2289,applicationChecks=27,applicationPresents=2289,
        frozenReferenceCaptureMatches=2,offlineMixedPcmFrames=app['pcmFrames'],offlinePcmHashMatchesFrozenReference=True,
        physicalAudioDevicesOpened=0,browserCompiledUnits=146,browserWasmSha256=browser['wasmSha256'],browserAcceptance=False,
        initialReplayConstructionStillSynchronous=True,defaultBrowserBackendAllStoresReady=True,
        originalGlobalSnapshotStillRestoredAsOneOperation=True,ordinaryBrowserIndependentSubstoreTimingAccepted=False,
        nativeRngValuesProvidedToEngine=False,oldRecordingExactThreadOrderRecovered=False,oldRngOrBulletFailuresClosed=False,
        completeGame=False,nativeEquivalent=False,
        limitations=['The instruction and sliced-loader matrices use synthetic RNG inputs and CPU schedules; the optional OS lock services are declared stand-ins.',
                     'The real GameSession tests deliberately delay readiness and inject one failure; they do not compare that changed schedule with a captured original run.',
                     'Initial replay creation is still synchronous, the normal browser backend defaults to all stores ready, and the global replay snapshot is restored as one operation.',
                     'The older unobserved RNG/camera/worldZ order, all-mode equivalence, source replay EOF, original full-game pixels/PCM, ordinary browser flows and persistence remain open.'],
        bindings=bindings,verifierSha256=sha(Path(__file__).read_bytes()))
    out=args.output.resolve();assert out.is_relative_to(R/'docs/porting')or out.is_relative_to(H)
    data=(json.dumps(result,indent=2)+'\n').encode()
    if args.check:assert out.read_bytes()==data
    else:out.write_bytes(data)
    print(json.dumps({key:value for key,value in result.items()if key not in('bindings','limitations','finiteRegressions')}))


if __name__=='__main__':main()
