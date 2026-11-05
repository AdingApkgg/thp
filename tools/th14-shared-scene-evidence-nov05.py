"""Check publishable shared-camera evidence; raw state and assets stay local."""
from pathlib import Path
import argparse, hashlib, json
R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/shared-scene-copy-nov05'
PUBLIC = R / 'docs/porting/th14-shared-scene-nov05.json'
SHA = lambda data: hashlib.sha256(data).hexdigest()


def collect():
    bindings = {}

    def raw(path):
        data = path.read_bytes()
        bindings[path.relative_to(R).as_posix()] = dict(bytes=len(data), sha256=SHA(data))
        return data

    def load(path):
        return json.loads(raw(path))

    def verify_raw_comparison(path):
        report = load(path)
        assert report['rawDataStructureAndReportedComparisonVerified'] and not report['liveSnapshotOnly']
        for name, item in report['evidenceBindings'].items():
            source = (R / name).resolve()
            assert source.is_relative_to(R / 'artifacts/th14')
            data = source.read_bytes()
            assert len(data) == item['bytes'] and SHA(data) == item['sha256'], name
        return report

    core = load(H / 'session-build/build.json')
    browser = load(H / 'browser-build/build.json')
    assert core['gameUnitsRecompiled'] == 141 and core['oldObjectsReused'] == 0
    assert browser['compiledUnits'] == 146 and browser['gameCoreObjectsRecompiled'] == 141 and browser['reusedObjectCount'] == 0
    assert core['sharedWasmMemory'] and browser['sharedWasmMemory'] and browser['sharedSceneCopyCandidate']
    for home, build, wasm in [(H / 'session-build', core, 'session.wasm'), (H / 'browser-build', browser, 'th14-sdl.wasm')]:
        assert SHA(raw(home / wasm)) == build['wasmSha256']
        for name, row in build['sourceBindings'].items():
            data = (home / 'source' / name).read_bytes()
            assert len(data) == row['bytes'] and SHA(data) == row['sha256'], name
        for name, digest in build['objectHashes'].items():
            assert SHA((home / 'objects' / (name.replace('/', '_') + '.o')).read_bytes()) == digest
    assert core['sharedSceneModuleFiles'] == {name: browser['independentRestoreModuleFiles'][name] for name in core['sharedSceneModuleFiles']}
    for name, row in core['sharedSceneModuleFiles'].items():
        assert SHA(raw(H / 'session-build' / name)) == row['sha256']
        assert SHA(raw(R / 'runtimes/th12/portable/sdl' / name)) == row['sha256']
    old_header = R / 'artifacts/th14/independent-full-session-nov05/build/source/th12_web/cpp/game/SceneCameraReadJobTh14.hpp'
    new_header = H / 'session-build/source/th12_web/cpp/game/SceneCameraReadJobTh14.hpp'
    def mapping(path):
        text = path.read_text(encoding='utf8')
        start = text.index('static u32 offset(')
        return text[start:text.index('\n    }', start)+6]
    assert mapping(old_header) == mapping(new_header)
    component_build = load(H / 'live-capture-component/build.json')
    component = load(H / 'live-capture-component/verified.json')
    assert SHA(raw(H / 'live-capture-component/component.wasm')) == component_build['wasmSha256'] == component['wasmSha256']
    assert component['independentPhysicalLiveReadsDuringBlockingCppCall'] and component['wordsFromInsideBlockingCall'] > 0
    assert component['cppDestinationMatchesWorkerWords'] == 75 and component['workerDoesNotWriteCppDestination']
    assert component['defaultSynchronous75WordsMatch'] and component['defaultWaitAndResume75WordsMatch']
    assert component['stickyDefaultReadFailureVerified'] and component['completedCppJobDoesNotReread']
    channel = load(H / 'channel-check-retry1/verified.json')
    assert channel['cases'] == 8 and channel['workersTerminal'] == 7 and channel['expectedFailureReports'] == 4
    assert channel['moduleBindings'] == core['sharedSceneModuleFiles']
    assert not channel['workerWritesCppDestination'] and not channel['perWordAcknowledgements']
    old_failure = load(H / 'channel-check/failure.json')
    assert not old_failure['passed'] and old_failure['kind'] == 'unsigned-i32-checker-interpretation'
    raw(H / 'channel-check/checker-initial.mjs')
    temp_log = raw(H / 'compiler-probe/compile.log')
    assert b'unable to make temporary file' in temp_log
    probe = load(H / 'compiler-probe-retry1/verified.json')
    assert probe['sharedWasmMemory'] and probe['workerDirectlyReadAndWroteActualWasmMemory']
    types = load(H / 'actual-memory-types.json')
    assert types['actualMemoryTypesVerified'] and types['unsharedControlPreserved']
    assert [row['memories'][0]['shared'] for row in types['rows']] == [False, True, True]
    syntax = load(H / 'shared-syntax/verified.json')
    assert len(syntax['cases']) == 9 and all(row['returncode'] == 0 for row in syntax['cases'])
    transport = load(H / 'transport.json')
    assert transport['verifiedTransport'] and transport['quietByDefault']
    assert transport['routes'] == 140 and len(transport['requests']) == 33
    requested = {row['path']: row for row in transport['requests']}
    for name in core['sharedSceneModuleFiles']:
        assert requested['/runtime/th14/' + name]['status'] == 200
    package = load(H / 'runtime/package-report.json')
    launcher = load(H / 'launcher/launcher-report.json')
    assert package['wasmSha256'] == launcher['wasmSha256'] == browser['wasmSha256']
    assert not package['browserAcceptance'] and not launcher['payloadFilesCopied']
    first = load(H / 'first-transition/report.json')
    assert first['terminal'] and first['stoppedBy'] == 'declared-callback-limit' and first['callbacks'] == 15000
    assert not first['errors'] and first['exception'] is None and first['cadenceMode'] == 'fast'
    assert first['sceneTasks'][0]['status'] == 2 and first['sceneTasks'][0]['copied'] == first['sceneTasks'][0]['successfulWords'] == 75
    first_raw = verify_raw_comparison(H / 'first-transition/raw-verified.json')
    assert not first_raw['strictOriginalPrefixPassed']
    full = load(H / 'full-loading-title/report.json')
    plan = load(H / 'full-loading-title/plan.json')
    assert full['terminal'] and full['stoppedBy'] == 'session-finished' and full['exception'] is None and not full['errors']
    assert full['realFrameCadenceAndClock'] and full['cadenceMode'] == 'real' and not full['directReplayEntry']
    assert full['gameObjectsReusedForThisFixtureLink'] == 141 and full['cppThreadSpawns'] == 0
    assert len(full['sceneTasks']) == len(full['producerTasks']) == 5 and full['workerThreadsTerminal'] == 10
    assert all(row['status'] == 2 and row['copied'] == row['successfulWords'] == 75 for row in full['sceneTasks'])
    assert all(row['ready'] == row['acknowledged'] == row['operations'] == 4 and row['statusBeforeCleanup'] == 2 for row in full['producerTasks'])
    assert [row['stage'] for row in full['stageEntries']] == [1, 2, 3, 4, 5, 6]
    assert SHA(raw(H / 'full-loading-title/driver.mjs')) == plan['bindings']['toolSha256'] == full['bindings']['toolSha256']
    assert SHA(raw(H / 'full-loading-title/observations.u32')) == full['observationsSha256']
    comparisons = {}
    for name in ['terminal-primary-raw.json', 'terminal-additional-full-raw.json']:
        result = verify_raw_comparison(H / 'full-loading-title' / name)
        assert not result['strictOriginalPrefixPassed'] and result['fullResourceOwnersFinishedWithFourOperations'] == 5
        comparisons[name] = dict(callbacksCompared=result['nativeComparedCallbacks'],
                                 selectedDifferenceFields=len(result['selectedDifferenceCounts']),
                                 cameraDifferenceFields=len(result['camera75DifferenceCounts']), hudDifferenceFields=len(result['hudDifferenceCounts']))
    pairs = load(H / 'full-loading-title/terminal-additional-full-109-pairs.json')
    assert pairs['verifiedDiagnosticPairing'] and not pairs['liveSnapshotOnly'] and not pairs['rawStrictGatesSuperseded']
    assert pairs['bindings']['modelSnapshotSha256'] == full['observationsSha256']
    boundary = load(H / 'full-loading-title/terminal-primary-boundaries.json')
    assert not boundary['liveSnapshotOnly'] and not boundary['rawStrictGatesSuperseded']
    log = raw(H / 'browser-build/link.log').decode('utf8', errors='replace')
    assert "'$invokeEntryPoint' depends on internal symbol '$runtimeKeepaliveCounter'" in log
    assert "'__pthread_create_js' depends on internal symbol '$pthreadCreateProxied'" in log
    source_files = ['runtimes/th12/th12_web/cpp/game/GameBattle.cpp', 'runtimes/th12/th12_web/cpp/game/GameSessionResources.cpp',
                    'runtimes/th12/th12_web/cpp/game/GameSessionResources.hpp', 'runtimes/th12/th12_web/cpp/game/SceneCameraReadJobTh14.hpp',
                    'runtimes/th12/th12_web/cpp/sdl/Application.cpp', 'runtimes/th12/portable/sdl/Th14AsyncRuntime.mjs',
                    'runtimes/th12/portable/sdl/Th14WebGpuRuntime.mjs', 'runtimes/th12/th12_web/tests/cpp/th14-shared-scene-session-nov05.cpp',
                    'runtimes/th12/th12_web/tests/cpp/th14-shared-scene-capture-nov05.cpp']
    for name in source_files:
        raw(R / name)
    result = dict(schema='th14/shared-scene-camera-evidence/1', evidenceIntegrityVerified=True,
                  featureEnabledInCandidate=True, defaultFeatureEnabled=False, freshWasiGameUnits=141, freshBrowserUnits=146,
                  wasiWasmSha256=core['wasmSha256'], browserWasmSha256=browser['wasmSha256'], actualSharedWasmMemoryTypesVerified=True,
                  oldUnsharedWasmControlPreserved=True, retailCameraOffsetMappingUnchanged=True,
                  workerPhysicallyReadsLiveCppCamera=True, workerWritesCppOwner=False, privateResultWords=75,
                  perCameraWordAcknowledgements=False, componentLiveWordsFromBlockingCppCall=component['wordsFromInsideBlockingCall'],
                  componentSynchronousCompatibility=True, completedCppReadJobDoesNotReread=True,
                  channelCases=8, channelWorkersTerminal=7, expectedRejectedInputCases=4,
                  retainedTemporaryDirectoryFailure=True, retainedCheckerI32Failure=True,
                  firstTransition=dict(callbacks=15000, declaredFastCadence=True, stoppedByDeclaredLimit=True, sceneWords=75,
                                       originalStrictPassed=False),
                  fullSession=dict(callbacks=full['callbacks'], stages=6, naturalSessionFinished=True, actualRealTimeCadence=True,
                                   loadingPreludeRealTime=False, cameraCaptures=5, cameraWords=375, workersTerminal=10,
                                   sceneTasks=full['sceneTasks'], rngTasks=full['producerTasks'],
                                   exactAll109WordPrefixCallbacks=boundary['exactAll109WordPrefixCallbacks'], firstDifference=boundary['firstDifference'],
                                   originalStrictPassed=False, comparisons=comparisons,
                                   additionalUniquePairs=pairs['uniquePairs'], selectedDifferenceFields=sorted(map(int, pairs['differenceCounts'])),
                                   shotCountDifferences=len(pairs['shotCountDifferences']), cameraDifferenceFields=len(pairs['camera75DifferenceCounts']),
                                   hudDifferenceFields=len(pairs['hudDifferenceCounts']), finalCursor=full['end'][8],
                                   finalStageDeclaredFrames=full['stageFrames'][5], inputFileEofAccepted=False),
                  sharedSyntaxCases=9, httpRequests=33, routes=140, quietByDefault=True,
                  browserCompilerInternalDependencyWarningsRetained=2, generatedResourcesCopied=False,
                  browserUiUnavailableThisTurn=True, browserAcceptance=False, inFlightBrowserCancellationAccepted=False,
                  nativeFrameVmTargetsUsed=False, originalObservationValuesWrittenToEngine=False,
                  gpuOrAudioEquivalenceAccepted=False, originalIndependentSchedulingAccepted=False,
                  strictModePassesAdded=0, wholeReplayAccepted=False, completeGame=False, nativeEquivalent=False,
                  evidenceBindings=bindings, toolSha256=SHA(Path(__file__).read_bytes()))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = collect()
    if args.check:
        assert json.loads(PUBLIC.read_bytes()) == result
    else:
        assert not PUBLIC.exists()
        PUBLIC.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps(dict(evidenceIntegrityVerified=True, sharedCameraWords=375, completeGame=False)))
