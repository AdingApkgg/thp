"""Bind the current TH14 hit-effect/owner checkpoint without promoting failures."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = 'docs/porting/th14-hit-effects-current-checkpoint-oct14.json'
MATRIX = 'docs/porting/th14-sanitized-input-parity-matrix-hit-effects-oct14-observed-oct14.json'
SHA = lambda data: hashlib.sha256(data).hexdigest()


def main():
    assert (ROOT / MATRIX).exists(), 'Current sanitizer matrix must finish before checkpoint publication'
    bindings, receipts = {}, {}

    def bind(name):
        path = (ROOT / name).resolve()
        assert path.is_relative_to(ROOT), str(path)
        key = path.relative_to(ROOT).as_posix()
        if key not in bindings:
            digest = hashlib.sha256()
            with path.open('rb') as stream:
                while chunk := stream.read(4 * 1024 * 1024):
                    digest.update(chunk)
            bindings[key] = dict(bytes=path.stat().st_size, sha256=digest.hexdigest())
        return path, bindings[key]

    def load(name):
        path, binding = bind(name)
        data = path.read_bytes()
        assert SHA(data) == binding['sha256'], str(path)
        return json.loads(data)

    def verify(name, digest, size=None):
        path, binding = bind(name)
        assert binding['sha256'] == digest, str(path)
        if size is not None:
            assert binding['bytes'] == size, str(path)

    def receipt(name, tool=None, hash_key='toolSha256'):
        report = load(name)
        assert not report['completeGame'] and not report['nativeEquivalent'], name
        for key in ('bindings', 'evidence'):
            bound = report.get(key, {})
            entries = bound.items() if isinstance(bound, dict) else ((row['path'], row) for row in bound)
            for path, entry in entries:
                verify(path, entry['sha256'], entry['bytes'])
        if tool:
            verify(tool, report[hash_key])
        receipts[name] = dict(bytes=bindings[name]['bytes'], sha256=bindings[name]['sha256'])
        return report

    engine_name = 'runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json'
    engine = load(engine_name)
    assert len(engine['sourceHashes']) == 265 and engine['engineSources'] == 141
    for name, digest in engine['sourceHashes'].items():
        verify('runtimes/th12/th12_web/' + name, digest)
    cases = []
    for label, title, frames, stage in (
        ('zps-normal-hit-effects-oct14', 'SakuyaA Normal', 96016, 6),
        ('zps-reimub-lunatic-hit-effects-oct14', 'ReimuB Lunatic', 98074, 6),
        ('zps-reimua-lunatic-hit-effects-oct14', 'ReimuA Lunatic', 90793, 6),
        ('zps-reimua-extra-hit-effects-oct14', 'ReimuA Extra', 39458, 7),
    ):
        directory = 'artifacts/th14/public-replay-playback/' + label
        playback = load(directory + '/report.json')
        assert playback['sourceHashes'] == engine['sourceHashes']
        assert (playback['frames'], playback['stage'], playback['candidatePlaybackEnded']) == (frames, stage, True)
        assert not playback['gameOverRequested'] and not playback['error'] and not playback['skipped'] and not playback['unsupported']
        assert playback['physicalInvocationOrder'] and playback['transitionCallbacksRetained']
        assert not playback['invulnerabilityOverride'] and not playback['forcedProgression']
        for name, key in (('selected-state.u32', 'selectedStateSha256'), ('callback-active.u8', 'callbackActiveSha256'),
                          ('public-replay.wasm', 'wasmSha256')):
            verify(directory + '/' + name, playback[key])
        for name, key in (('th14-public-replay-physical-fixture.cpp', 'fixtureSha256'),
                          ('th14-custom-replay-reference-fixture.cpp', 'includedFixtureSha256'),
                          ('th14-session-reference-fixture.cpp', 'sessionFixtureSha256')):
            verify('runtimes/th12/th12_web/tests/cpp/' + name, playback[key])
        verify('tools/th14-public-replay-physical-playback-check.mjs', playback['toolSha256'])
        cases.append(dict(title=title, frames=frames, stage=stage, candidatePlaybackEnded=True,
                          gameOver=False, nativeEquivalent=False, replaySha256=playback['replaySha256']))

    combat = receipt('docs/porting/th14-hit-effects-full-combat-verified-oct14.json',
                     'tools/th14-hit-effects-full-combat-evidence-check.py', 'verifierSha256')
    assert combat['diagnosticEvidenceVerified'] and not combat['comparisonPassed']
    assert combat['sourceHashes'] == engine['sourceHashes'] and combat['comparedCallbacks'] == 90793
    assert combat['allNativeCallbacksPaired'] and combat['unpairedNativeCallbacks'] == 0
    assert (combat['rawGameplayDifferences'], combat['rawVisualDifferences'], combat['retainedDetailDifferences']) == (25, 181570, 80)
    assert (combat['inactiveLoadingDetailDifferences'], combat['activeBattleDetailDifferences']) == (72, 8)
    assert combat['activeAreaDifferenceColumnCounts'] == {'8': 8}
    assert combat['inactiveLoadingDetailDifferenceKinds'] == {'enemyNextId': 72}
    assert combat['activeBattleDetailDifferenceKinds'] == {'damageAreas': 8}
    assert len(combat['rawGameplayDifferenceRecords']) == 25 and len(combat['detailDifferenceRecords']) == 80
    assert len(combat['activeAreaPositionZDifferenceRecords']) == 8
    assert len(combat['equalSelectedGameplayFields']) == 29
    assert combat['activeLateWindowCallbacks'] == {'4': 71, '5': 71, '6': 71}
    z_consumers = receipt('docs/porting/th14-damage-area-z-consumer-verified-oct14.json',
                          'tools/th14-damage-area-z-consumer-evidence-check.py', 'verifierSha256')
    assert z_consumers['diagnosticEvidenceVerified'] and z_consumers['collectorCases'] == 48
    assert z_consumers['controlledCallbacksDisabled'] and z_consumers['originalInstructionsUnmodified']
    assert z_consumers['allDamageAndScoreIndependentOfTestedZWords'] and z_consumers['areaZCopiedToLastHitOutput']

    visual = receipt('docs/porting/th14-hit-effect-current-visual-verified-oct14.json',
                     'tools/th14-hit-effect-current-visual-evidence-check.py')
    assert visual['diagnosticEvidenceVerified'] and not visual['passed'] and visual['sourceFilesVerified'] == 265
    assert visual['comparedCallbacks'] == 90793 and visual['fieldDifferenceCounts'] == {
        'visualSeed': 90777, 'visualCalls': 90793, 'gameplayCalls': 25}
    increments = visual['visualIncrementDiagnostic']
    assert increments['doesNotModifyAbsoluteEquality'] and increments['comparisons'] == 90792
    assert (increments['beforeDifferences'], increments['currentDifferences']) == (18712, 10920)
    for record in (visual['allAbsoluteDifferences'], increments['allCurrentIncrementDifferences']):
        verify(record['path'], record['sha256'], record['bytes'])

    fanout = receipt('docs/porting/th14-bullet-cancel-visual-fanout-verified-oct14.json',
                     'tools/th14-bullet-cancel-visual-fanout-evidence-check.py')
    assert fanout['passed'] and fanout['isolatedControlsOnly'] and not fanout['fullCampaignRngChanged']
    assert (fanout['sourceFilesVerified'], fanout['rootsPerControl'], fanout['updatesAfterFactory'], fanout['matchedTimelines']) == (265, 240, 16, 34)
    assert fanout['freshModuleAndNativeEmulatorPerControl'] and fanout['completeTwoWaveVisualCallsPerControl'] == [9600, 9600]
    assert len(fanout['controls']) == 2 and all(len(row['timeline']) == 17 for row in fanout['controls'])
    assert fanout['fullCampaignIncrementDifferencesRetained'] == 10920

    normal = receipt('docs/porting/th14-normal-continuous-hit-effects-oct14.json',
                     'tools/th14-continuous-retail-compact-evidence-check.py', 'verifierSha256')
    extra = receipt('docs/porting/th14-extra-continuous-hit-effects-oct14.json',
                    'tools/th14-continuous-retail-compact-evidence-check.py', 'verifierSha256')
    assert not normal['passed'] and normal['comparedCallbacks'] == 96016 and normal['gameplayDifferences'] == 25
    assert len(normal['equalSelectedGameplayFields']) == 29 and normal['allRemainingGameplayDifferencesDuringInactiveLoading']
    assert extra['passed'] and extra['comparedCallbacks'] == 39458 and extra['gameplayDifferences'] == 0
    assert len(extra['equalSelectedGameplayFields']) == 30
    for row in (normal, extra):
        assert row['sourceFilesVerified'] == 265 and row['candidatePlaybackEnded']
        verify(row['allDifferences']['path'], row['allDifferences']['sha256'], row['allDifferences']['bytes'])

    storage = receipt('docs/porting/th14-natural-storage-normal-sakuyaa-hit-effects-oct14-verified-oct14.json',
                      'tools/th14-normal-hit-effects-storage-evidence-check.mjs', 'evidenceCheckerSha256')
    assert storage['diagnosticEvidenceVerified'] and storage['passed'] and storage['sourceFilesVerified'] == 265
    assert (storage['naturalInputFrames'], storage['endingIndex'], storage['endingFrames']) == (95220, 5, 3737)
    assert (storage['scoreBytes'], storage['rawBytes'], storage['clearCount'], storage['noContinueClearCount']) == (22379, 149076, 1, 1)
    assert storage['native']['passed'] and not storage['forcedProgression'] and not storage['invulnerabilityOverride']
    ordinary = receipt('docs/porting/th14-natural-current-replay-normal-hit-effects-verified-oct14.json',
                       'tools/th14-normal-hit-effects-replay-evidence-check.mjs')
    assert ordinary['diagnosticEvidenceVerified'] and ordinary['naturalInputFrames'] == 95220
    assert (ordinary['activeDifferentWords'], ordinary['inactiveScoreDifferentWords']) == (0, 10)

    sanitizer = receipt('docs/porting/th14-sanitized-replay-hit-effects-oct14-observed-oct13.json',
                        'tools/th14-sanitized-replay-check.mjs')
    matrix = receipt(MATRIX, 'tools/th14-sanitized-hit-effects-matrix-check.mjs')
    assert sanitizer['passed'] and sanitizer['frames'] == 96016 and not sanitizer['errors'] and not sanitizer['gameOver']
    assert sanitizer['sourceHashes'] == matrix['sourceHashes'] == engine['sourceHashes']
    verify('runtimes/th12/th12_web/tests/cpp/th14-public-replay-physical-fixture.cpp', matrix['fixtureSha256'])
    assert sanitizer['fixtureSha256'] == matrix['fixtureSha256']
    assert matrix['sanitizerMatrixVerified'] and len(matrix['cases']) == 3
    assert [(row['frames'], row['stage']) for row in matrix['cases']] == [(90793, 6), (98074, 6), (39458, 7)]
    assert all(row['sanitizerPassed'] and row['candidatePlaybackEnded'] and not row['gameOver'] and not row['errors'] for row in matrix['cases'])
    directory = 'artifacts/th14/sanitized-replay/hit-effects-oct14/'
    compile_build = load(directory + 'compile-build.json')
    assert compile_build['sourceHashes'] == engine['sourceHashes'] and len(compile_build['objectSha256']) == 141
    verify(directory + 'compile-build.json', matrix['compileBuildSha256'])
    verify(directory + 'sanitized.mjs', matrix['loaderSha256'])
    verify(directory + 'sanitized.wasm', matrix['wasmSha256'], matrix['wasmBytes'])
    assert sanitizer['wasmSha256'] == matrix['wasmSha256']
    assert '-fsanitize=address,undefined' in matrix['sanitizerFlags'] and '-fno-sanitize-recover=all' in matrix['sanitizerFlags']
    for path, digest in compile_build['objectSha256'].items():
        verify(path, digest)

    browser = receipt('docs/porting/th14-hit-effects-browser-flow-verified-oct14.json',
                      'tools/th14-hit-effects-browser-flow-evidence-check.mjs')
    assert browser['observedBrowserFlowVerified'] and browser['replayFrames'] == 468
    assert browser['recordedUnderPreviousBuild'] and (browser['consoleWarnings'], browser['consoleErrors']) == (2, 0)
    assert len(browser['consoleEntries']) == 2 and all(row['level'] == 'warn' for row in browser['consoleEntries'])
    sdl = load('runtimes/th14/th14_web/artifacts/sdl3-release/build.json')
    assert browser['build'] == sdl and sdl['bytes'] == 1872163
    assert sdl['sha256'] == 'c36863500ff398f14dea90217eb65ef6b6d266128288934b746b0d18c5fb35f2'
    verify('runtimes/th14/th14_web/artifacts/sdl3-release/th11.wasm', sdl['sha256'], sdl['bytes'])
    assert (len(sdl['sources']), len(sdl['headers'])) == (146, 144)
    for name, digest in {**sdl['sources'], **sdl['headers']}.items():
        verify('runtimes/th12/' + name, digest)
    for name in ('docs/porting/th14-launcher-runtime-prepared-hit-effects-oct14.json',
                 'docs/porting/th14-launcher-preview-prepared-hit-effects-oct14.json'):
        prepared = receipt(name)
        assert prepared['passed']

    result = dict(diagnosticCheckpointVerified=True, completeGame=False, nativeEquivalent=False,
        sourceFilesVerified=265, sourceHashes=engine['sourceHashes'], cases=cases,
        lunaticNativeCaptureBudget=90793, lunaticNativeCapturedCallbacks=90793, lunaticNativeOrdinaryTerminalVerified=False,
        lunaticEqualGameplayFields=29, lunaticLoadingGameplayDifferences=25, lunaticAbsoluteVisualDifferences=181570,
        lunaticRetainedDetailDifferences=80, lunaticLoadingEnemyNextIdDifferences=72, lunaticActiveAreaZWordDifferences=8,
        lunaticActiveAreaOwnerMetadataDifferences=0, visualIncrementDiagnosticBefore=18712,
        originalZConsumerControlCases=48, originalAreaZOutputRemainsObservable=True,
        visualIncrementDiagnosticCurrent=10920, visualIncrementDiagnosticDoesNotChangeAbsoluteEquality=True,
        isolatedBulletCancelControlRoots=240, isolatedBulletCancelControls=2, isolatedBulletCancelUpdates=16,
        isolatedBulletCancelMatchedTimelines=34, isolatedBulletCancelProofChangesCampaign=False,
        normalNativeCallbacks=96016, normalEqualGameplayFields=29, normalLoadingGameplayDifferences=25,
        extraNativeCallbacks=39458, extraEqualGameplayFields=30, extraGameplayDifferences=0,
        extraAbsoluteVisualDifferences=78916, ordinaryNaturalInputFrames=95220, ordinaryEndingFrames=3737,
        ordinaryScoreBytes=22379, ordinaryDecodedScoreBytes=149076,
        ordinaryRecordedReplayActiveDifferentWords=0, ordinaryRecordedReplayInactiveScoreDifferentWords=10,
        sanitizerCases=[dict(title='SakuyaA Normal', frames=96016, passed=True), *matrix['cases']],
        browserReplayFrames=468, browserRecordedUnderPreviousBuild=True, browserPersistenceAcrossBuildUpdateObserved=True,
        browserConsoleWarnings=2, browserConsoleErrors=0,
        sdl=dict(bytes=sdl['bytes'], sha256=sdl['sha256'], sources=146, headers=144),
        publicEvidenceReceipts=receipts, bindings=bindings, toolSha256=SHA(Path(__file__).read_bytes()),
        scope='Current owner retention matches original allocator memory behavior; focused/plain hit factories use original effect.anm file 8 and retained template layer -1. Four intact public inputs naturally finish current production and nonrecovering ASAN/UBSan. The 90,793 original Lunatic callbacks reach the requested capture budget, which is not evidence of an ordinary Native terminal or ending. 29 selected gameplay fields agree; 25 loading gameplay-call, 72 loading enemyNextId, 8 active raw area Z and 181,570 absolute visual RNG differences remain unmasked. The original ReimuA path reads an unwritten third polar output word; the actual stack writers responsible for those 8 captured values are not dynamically established. Controlled 2D collision Z independence does not hide observable lastHit Z output. Visual increment mismatches fall from 18,712 to 10,920 only in a separately labeled diagnostic, not absolute equality. Two fresh 240-root bullet199 controls match 34 timelines through 16 updates under identical declared prestates; this does not rewrite full-campaign RNG or prove cancellation rendering. Normal retains 25 loading differences; Extra has 30 selected gameplay fields equal with 78,916 absolute visual failures retained. One declared warm Replay initialization remains. Current ordinary 95,220-input clear, ending/results/storage and original 22,379/149,076 score codec are bound; recorded replay retains 10 inactive score-restoration differences. Browser plays a previously saved 468-frame recording across the release update and returns normally; two Launcher update warnings remain and recording was not saved anew under this build. All modes, original menu/loading lifecycle, complete owner memory, visual RNG, pixels/audio and whole-game 1:1 remain unfinished. Historical receipts remain historical.')
    (ROOT / OUTPUT).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in ('diagnosticCheckpointVerified', 'sourceFilesVerified',
        'lunaticNativeCapturedCallbacks', 'lunaticRetainedDetailDifferences', 'visualIncrementDiagnosticCurrent',
        'ordinaryNaturalInputFrames', 'ordinaryScoreBytes', 'browserConsoleWarnings', 'browserConsoleErrors')}))


if __name__ == '__main__':
    main()
