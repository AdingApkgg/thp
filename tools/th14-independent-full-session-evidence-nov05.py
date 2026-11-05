"""Publishable counts and hashes for the independent full-session experiment.

Only terminal session reports are eligible. Assets, observations, native state,
RNG values, replay data and binaries remain local. This accepts evidence
integrity, never original scheduling, complete-game fidelity or strict modes.
"""
from pathlib import Path
import argparse, hashlib, json

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/independent-full-session-nov05'
PUBLIC = R / 'docs/porting/th14-independent-full-session-nov05.json'
SHA = lambda data: hashlib.sha256(data).hexdigest()


def collect():
    bindings = {}

    def raw(path):
        data = path.read_bytes()
        bindings[path.relative_to(R).as_posix()] = dict(bytes=len(data), sha256=SHA(data))
        return data

    def load(path):
        return json.loads(raw(path))

    def verify_bindings(item, key='evidenceBindings'):
        for name, expected in item[key].items():
            path = (R / name).resolve()
            assert path.is_relative_to(R / 'artifacts/th14')
            data = path.read_bytes()
            assert len(data) == expected['bytes'] and SHA(data) == expected['sha256'], name

    build = load(H / 'build/build.json')
    assert build['compiled'] and build['gameUnitsRecompiled'] == 141 and build['oldObjectsReused'] == 0
    assert SHA(raw(H / 'build/session.wasm')) == build['wasmSha256']
    fixture = raw(R / build['fixturePath'])
    assert SHA(fixture) == build['fixtureSha256'] and raw(H / 'build/fixture.cpp') == fixture
    for name, digest in build['objectHashes'].items():
        assert SHA((H / 'build/objects' / (name.replace('/', '_') + '.o')).read_bytes()) == digest
    assert len(build['objectHashes']) == 141
    for name, info in build['sourceBindings'].items():
        data = (R / build['sourceSnapshotRoot'] / name).read_bytes()
        assert len(data) == info['bytes'] and SHA(data) == info['sha256']
    probe = load(H / 'queued-loading-title-session/build.json')
    assert probe['baseBuildSha256'] == bindings[(H / 'build/build.json').relative_to(R).as_posix()]['sha256']
    assert probe['gameObjectsReused'] == 141 and probe['actualGameSessionTitleAndAttractPath']
    assert SHA(raw(H / 'queued-loading-title-session/probe.wasm')) == probe['wasmSha256']
    assert SHA(raw(H / 'queued-loading-title-session/fixture.cpp')) == probe['fixtureSha256']
    assert SHA(raw(R / 'tools/th14-probe-session-title-entry-nov05.py')) == probe['toolSha256']
    first = load(H / 'queued-loading-title-session/verified-prefix-profile.json')
    retained_other = load(H / 'queued-loading-title-session/verified.json')
    other = load(H / 'queued-loading-title-session/full-native-current-checker.json')
    assert first['successfulEntry'] and not first['firstSelectedDifferenceFields']
    assert other['successfulEntry'] and other['firstSelectedDifferenceFields'] == [21, 22]
    assert retained_other['firstSelectedDifferenceFields'] == other['firstSelectedDifferenceFields']
    assert first['buildSha256'] == other['buildSha256'] == bindings[(H / 'queued-loading-title-session/build.json').relative_to(R).as_posix()]['sha256']
    assert not first['scriptSeedCounterPreset'] and not other['scriptSeedCounterPreset']
    assert SHA(raw(R / 'tools/th14-check-session-title-entry-nov05.mjs')) == first['toolSha256']
    assert first['toolSha256'] == other['toolSha256']
    sessions = {}
    for label, directory, direct in [('directControl', 'run-retry2', True), ('loadingTitle', 'run-loading-title', False)]:
        home = H / directory
        report = load(home / 'report.json')
        plan = load(home / 'plan.json')
        assert report['terminal'] and report['stoppedBy'] == 'session-finished' and report['exception'] is None
        assert not report['errors'] and [row['stage'] for row in report['stageEntries']] == [1, 2, 3, 4, 5, 6]
        assert report['workerThreadsTerminal'] == 5 and len(report['producerTasks']) == 5
        assert all(row['operations'] == row['ready'] == row['acknowledged'] == 4 and row['statusBeforeCleanup'] == 2 for row in report['producerTasks'])
        assert SHA(raw(home / 'driver.mjs')) == plan['bindings']['toolSha256'] == report['bindings']['toolSha256']
        if direct:
            assert SHA(raw(R / 'tools/th14-run-independent-session-direct-control-nov05.mjs')) == plan['bindings']['toolSha256']
        assert SHA(raw(home / 'observations.u32')) == report['observationsSha256']
        assert not report['strictOriginalPrefixPassed'] and not report['wholeReplayAcceptance']
        comparisons = {}
        for name in ['terminal-primary-raw.json', 'terminal-additional-full-raw.json', 'terminal-additional-full-109-pairs.json']:
            item = load(home / name)
            if 'rawDataStructureAndReportedComparisonVerified' in item:
                assert item['rawDataStructureAndReportedComparisonVerified'] and not item['liveSnapshotOnly']
                verify_bindings(item)
                assert not item['strictOriginalPrefixPassed'] and item['fullResourceOwnersFinishedWithFourOperations'] == 5
                comparisons[name] = dict(callbacks=item['callbacksVerified'], compared=item['nativeComparedCallbacks'],
                                         selectedDifferenceFields=len(item['selectedDifferenceCounts']),
                                         cameraDifferenceFields=len(item['camera75DifferenceCounts']), hudDifferenceFields=len(item['hudDifferenceCounts']))
            else:
                assert item['verifiedDiagnosticPairing'] and not item['liveSnapshotOnly']
                assert item['toolSha256'] == SHA(raw(R / 'tools/th14-independent-session-stage-pairs-nov05.py'))
                assert item['bindings']['modelSnapshotSha256'] == report['observationsSha256']
                comparisons[name] = dict(uniquePairs=item['uniquePairs'], differenceFields=sorted(map(int, item['differenceCounts'])),
                                         shotCountDifferences=len(item['shotCountDifferences']),
                                         cameraDifferenceFields=len(item['camera75DifferenceCounts']), hudDifferenceFields=len(item['hudDifferenceCounts']))
        boundary = load(home / 'terminal-primary-boundaries.json')
        verify_bindings(boundary, 'bindings')
        assert boundary['callbacksCompared'] == 35000 and not boundary['liveSnapshotOnly']
        assert not boundary['rawStrictGatesSuperseded'] and not boundary['referenceValuesWrittenToEngine']
        sessions[label] = dict(callbacks=report['callbacks'], stages=6, elapsedSeconds=report['elapsedSeconds'],
                               directReplayEntry=direct, fourStepResourceCompletions=5, workerThreadsTerminal=5,
                               successfulProducerStatusBeforeCleanup=[row['statusBeforeCleanup'] for row in report['producerTasks']],
                               exactAll109WordPrefixCallbacks=boundary['exactAll109WordPrefixCallbacks'],
                               firstDifference=boundary['firstDifference'], strictOriginalPrefixPassed=False,
                               selectedStageAtFinish=report['end'][1],
                               finalReplayCursor=report['end'][8], finalStageDeclaredFrames=report['stageFrames'][5],
                               declaredFramesBeyondFinalCursor=report['stageFrames'][5]-report['end'][8],
                               inputFileEofAccepted=False, nativeObservedSleepIntervals=boundary['nativeObservedSleepIntervals'],
                               comparisons=comparisons)
    for name in ['run/failure.json', 'run-retry1/failure.json']:
        failure = load(H / name)
        assert failure
    aggregate_failure = load(H / 'evidence-checker-initial-failure.json')
    assert aggregate_failure['kind'] == 'metadata-key-mismatch' and not aggregate_failure['passed']
    raw(H / 'evidence-checker-initial.py')
    for name in ['tools/th14-build-independent-session-nov05.py', 'tools/th14-run-independent-session-nov05.mjs',
                 'tools/th14-verify-independent-session-nov05.py', 'tools/th14-independent-session-boundaries-nov05.py']:
        raw(R / name)
    result = dict(schema='th14/independent-full-session-evidence/1', evidenceIntegrityVerified=True,
                  gameUnitsFreshlyRecompiled=141, oldObjectsReusedInCoreBuild=0, coreWasmSha256=build['wasmSha256'],
                  loadingPreludeWasmSha256=probe['wasmSha256'], sessions=sessions,
                  loadingPrelude=dict(actualTitleAndAttractPath=True, actualSdlStartupDrawMethod=True,
                                      realTextureChunkConversion=True, firstPrefixProfile32WordsMatch=True,
                                      additionalFullNativeProfileDifferenceFields=other['firstSelectedDifferenceFields'],
                                      initialScriptCallCountDifference=first['nativeFirstScriptCalls']-other['nativeFirstScriptCalls'],
                                      rngSeedOrCounterPreset=False, fullColdApplicationAccepted=False),
                  initializationFailuresRetained=2, aggregateCheckerKeyMismatchFailureRetained=True,
                  nativeFrameOrVmReadyTargetsUsed=False,
                  originalObservationValuesWrittenToEngine=False, extraAckSynchronizationCostUncalibrated=True,
                  rawPhysicalOrderGatesSuperseded=False, strictModePassesAdded=0,
                  bootstrapRealTimeCadence=False, gpuOrAudioDeviceExecuted=False,
                  browserCrossStageAcceptance=False, originalIndependentSchedulingAccepted=False,
                  wholeReplayAccepted=False, completeGame=False, nativeEquivalent=False, evidenceBindings=bindings)
    result['toolSha256'] = SHA(Path(__file__).read_bytes())
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
    print(json.dumps(dict(evidenceIntegrityVerified=True, terminalSessions=2, completeGame=False)))
