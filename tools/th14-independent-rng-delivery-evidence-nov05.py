"""Publish protocol counts and bindings, never original assets or raw RNG rows."""
from pathlib import Path
import argparse,hashlib,json
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/independent-rng-delivery-nov05'
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def verify():
    bindings={}
    def raw(path):
        data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
    def read(path):return json.loads(raw(path))
    home=H/'component-retry1';build=read(home/'build.json');run=read(home/'verified.json')
    assert build['compiled'] and run['passed'] and build['wasmSha256']==run['wasmSha256']
    assert SHA(raw(home/'component.wasm'))==build['wasmSha256']
    assert SHA(raw(home/'fixture.cpp'))==build['fixtureSha256']
    for name,key in [('worker.mjs','workerSha256'),('driver.mjs','driverSha256'),('build-tool.py','toolSha256')]:
        assert SHA(raw(home/name))==build[key]
    for name,digest in build['headerHashes'].items():
        assert SHA(raw(home/name))==digest
        assert SHA(raw(R/'runtimes/th12/th12_web/cpp/game'/name))==digest
    assert build['fixtureSha256']==SHA(raw(R/'runtimes/th12/th12_web/tests/cpp/th14-independent-rng-delivery-nov05.cpp'))
    assert build['workerSha256']==SHA(raw(R/'tools/th14-independent-rng-delivery-worker-nov05.mjs'))
    assert run['realProductionRestoreJob'] and run['realProductionRngNext32'] and run['syntheticInputsOnly']
    assert not run['producerSuppliesRngWords'] and not run['producerSuppliesFrameOrVmIdentity']
    assert not run['sharedWasmMemoryRequired'] and not run['ordinaryApplicationIntegrated']
    by_name={case['name']:case for case in run['cases']};assert len(by_name)==6
    baseline=by_name['same-thread-timer'];assert baseline['blocked']['stores']==0
    assert baseline['blocked']['elapsedUs']>=120000 and baseline['yielded']['stores']==3
    names=['BeforeRead','SeedRead','CounterCommitted','BeforeStore','SeedWritten']
    workers=[]
    for name in ['worker-a','worker-b','worker-c']:
        case=by_name[name];state=case['observed']
        assert state['complete'] and state['stores']==state['commits']==case['commitsBeforeSynchronousReturn']==3
        assert case['workerStatus']==2 and not state['invalid'] and not state['observerStillInstalled']
        workers.append(dict(name=name,stores=3,iterations=state['iterations'],elapsedUs=state['elapsedUs'],
            observedBoundaries=[names[row[1]]for row in state['commitRows']],
            observedScriptSeedBoundary=names[state['commitRows'][1][1]]))
    cancelled=by_name['cancel-after-script']['observed'];stale=by_name['stale-generation']['observed']
    assert cancelled['stores']==2 and cancelled['progress']==2 and cancelled['gameCalls']==19
    assert stale['stores']==0 and stale['progress']==2
    native=read(H/'native-check-retry1/verified.json')
    assert native['passed'] and native['inputSha256']==SHA(raw(home/'verified.json'))
    assert native['allCapturedCallsEqual'] and native['capturedSyntheticCalls']==12
    assert native['capturedWorkerCalls']==9 and native['negativeControls']==native['negativeRejected']==5
    assert native['syntheticInputsOnly'] and not native['originalWindowsProcessRun']
    failed=read(H/'native-check/failure.json')
    assert failed['actual'][0]==(failed['expected'][0]&0xffffffff)
    assert failed['actual'][1:]==failed['expected'][1:]
    raw(H/'native-check/checker.py');raw(H/'component/verified.json')
    for name in ['worker.mjs','driver.mjs','build-tool.py']:raw(H/'component'/name)
    assert b'Atomics.wait(state,3,Atomics.load(state,3),100)'in raw(H/'component/worker.mjs')
    assert b'Atomics.wait(state,3,acknowledged,100)'in raw(home/'worker.mjs')
    for name in ['th14-independent-rng-delivery-build-nov05.py','th14-independent-rng-delivery-check-nov05.mjs',
                 'th14-independent-rng-delivery-native-nov05.py']:raw(R/'tools'/name)
    return dict(schema='th14/independent-rng-delivery-public-evidence/1',
        verifiedIndependentProducerProtocolComponent=True,
        realProductionRestoreJobAndRng=True,syntheticInputsOnly=True,
        sourceRole='Component experiment over unchanged production headers; not ordinary Application integration.',
        wasmSha256=build['wasmSha256'],engineObjectsRecompiled=0,
        sameThreadTimer=dict(storesBeforeSynchronousReturn=0,blockingWindowUs=baseline['blocked']['elapsedUs'],
            storesAfterYield=3),independentWorkers=workers,
        producerHasNoRngWordsOrFrameVmTargets=True,
        cancelledAfterScriptStore=dict(stores=2,counterClearPrevented=True,failedJob=True),
        staleGeneration=dict(stores=0,failedJob=True),
        nativeComponent=dict(capturedCalls=12,capturedIndependentWorkerCalls=9,wordsPerCall=4,
            all48WordsEqual=True,retailArithmeticPackingAndScriptSeedStoreExecuted=True,
            alteredBoundaryControls=5,alteredBoundaryControlsRejected=5,
            comparison='Packed return, ending seed, ending counter, retained input; same captured Wasm calls unchanged.',
            originalExecutableSha256=native['executableSha256'],controlledEmulatorCriticalSectionBoundary=True,
            realOriginalProcessOrSchedulerAccepted=False),
        initialPrototypeRetained=True,ackWaitPredicateRaceCorrected=True,
        old100msPauseCauseUniquelyProven=False,
        initialNativeCheckerSignedI32FailureRetained=True,rawRowsUnchangedForU32Interpretation=True,
        currentDriverExportsUnsignedWords=True,frozenExecutedDriverUsedSignedI32Exports=True,
        sharedWasmMemoryOrPthreadRebuildRequiredForThisComponent=False,
        producerWaitsForMainStoreAcknowledgements=True,extraSynchronizationCostUncalibrated=True,
        ordinaryApplicationIntegrated=False,replayGlobalSnapshotDeliveryTested=False,
        originalIndependentSchedulingAccepted=False,wholeReplayCompared=False,
        formalGameplaySourcesChanged=False,modePassCountsChanged=False,
        originalWindowsProcessStarted=False,browserOrAudioDeviceOpened=False,
        completeGame=False,nativeEquivalent=False,rawAssetsOrObservationsUploaded=False,
        evidenceBindings=bindings,toolSha256=SHA(Path(__file__).read_bytes()))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    result=verify();target=R/'docs/porting/th14-independent-rng-delivery-nov05.json'
    if a.check:assert json.loads(target.read_bytes())==result
    else:target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(independentWorkerComponent=True,workerRuns=3,nativeCalls=12,
        alteredBoundaryRejected=5,ordinaryApplicationIntegrated=False,completeGame=False)))
