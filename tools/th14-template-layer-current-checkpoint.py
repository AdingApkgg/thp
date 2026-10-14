"""Bind the current TH14 template-layer/package checkpoint without promoting failures."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = 'docs/porting/th14-template-layer-current-checkpoint-oct14.json'
MATRIX = 'docs/porting/th14-sanitized-input-parity-matrix-template-layer-oct14-observed-oct14.json'
SHA = lambda data: hashlib.sha256(data).hexdigest()


def main():
    required = [MATRIX,
        'docs/porting/th14-template-layer-browser-flow-verified-oct14.json',
        'docs/porting/th14-natural-storage-normal-sakuyaa-template-layer-oct14-verified-oct14.json',
        'docs/porting/th14-natural-current-replay-normal-template-layer-verified-oct14.json']
    missing = [name for name in required if not (ROOT / name).exists()]
    assert not missing, 'Current receipts must finish before checkpoint generation: ' + ', '.join(missing)
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
        ('zps-normal-template-layer-oct14', 'SakuyaA Normal', 96016, 6),
        ('zps-reimub-lunatic-template-layer-oct14', 'ReimuB Lunatic', 98074, 6),
        ('zps-reimua-lunatic-template-layer-oct14', 'ReimuA Lunatic', 90793, 6),
        ('zps-reimua-extra-template-layer-oct14', 'ReimuA Extra', 39458, 7),
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

    combat = receipt('docs/porting/th14-template-layer-full-combat-verified-oct14.json',
                     'tools/th14-template-layer-full-combat-evidence-check.py', 'verifierSha256')
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

    layers = receipt('docs/porting/th14-effect-template-layer-current-verified-oct14.json',
                     'tools/th14-effect-template-layer-current-evidence-check.py')
    assert layers['passed'] and not layers['productionModifiedByVerifier'] and layers['sourceFilesVerified'] == 265
    assert layers['actualProductionCallerCases'] == 7 and layers['originalNativeFactoryControlsReused'] == 14
    assert len(layers['observations']) == 7
    assert layers['nativeExpectedLayers'] == {'reimu-bomb-hit': 20, 'curve-graze': 18,
        'item-spawn-notice': 16, 'player-death': 18, 'player-hit': 18,
        'bullet-cancel': 21, 'player-focus-correct-control': 14}
    clock = receipt('docs/porting/th14-startup-platform-clock-verified-oct14.json',
                    'tools/th14-startup-platform-clock-evidence-check.py')
    assert clock['passed'] and not clock['productionClockFixNeeded'] and not clock['campaignSeedOrCounterChanged']
    assert clock['matchedClockStoreCases'] == 6 and not clock['directBootstrapClockObservation']['inferredFromRng']
    clock_sources = load('artifacts/th14/startup-platform-clock-oct14/source-snapshots.json')
    for name, digest in clock_sources['sourceHashes'].items():
        verify('runtimes/th12/th12_web/' + name, digest)
    # Prior diagnostic receipts remain immutable history. Their old engine and
    # C++ bindings are deliberately not revalidated or promoted to this source.
    historical = {}
    for name in ('docs/porting/th14-hit-effects-current-checkpoint-oct14.json',
                 'docs/porting/th14-hit-effect-current-visual-verified-oct14.json',
                 'docs/porting/th14-bullet-cancel-visual-fanout-verified-oct14.json'):
        old = load(name)
        assert not old['completeGame'] and not old['nativeEquivalent']
        historical[name] = {**bindings[name], 'currentSourcePassClaimed': False}

    normal = receipt('docs/porting/th14-normal-continuous-template-layer-oct14.json',
                     'tools/th14-continuous-retail-compact-evidence-check.py', 'verifierSha256')
    extra = receipt('docs/porting/th14-extra-continuous-template-layer-oct14.json',
                    'tools/th14-continuous-retail-compact-evidence-check.py', 'verifierSha256')
    assert not normal['passed'] and normal['comparedCallbacks'] == 96016 and normal['gameplayDifferences'] == 25
    assert len(normal['equalSelectedGameplayFields']) == 29 and normal['allRemainingGameplayDifferencesDuringInactiveLoading']
    assert extra['passed'] and extra['comparedCallbacks'] == 39458 and extra['gameplayDifferences'] == 0
    assert len(extra['equalSelectedGameplayFields']) == 30
    for row in (normal, extra):
        assert row['sourceFilesVerified'] == 265 and row['candidatePlaybackEnded']
        verify(row['allDifferences']['path'], row['allDifferences']['sha256'], row['allDifferences']['bytes'])

    storage = receipt('docs/porting/th14-natural-storage-normal-sakuyaa-template-layer-oct14-verified-oct14.json',
                      'tools/th14-normal-template-layer-storage-evidence-check.mjs', 'evidenceCheckerSha256')
    assert storage['diagnosticEvidenceVerified'] and storage['passed'] and storage['sourceFilesVerified'] == 265
    assert (storage['naturalInputFrames'], storage['endingIndex'], storage['endingFrames']) == (95220, 5, 3737)
    assert (storage['scoreBytes'], storage['rawBytes'], storage['clearCount'], storage['noContinueClearCount']) == (22379, 149076, 1, 1)
    assert storage['native']['passed'] and not storage['forcedProgression'] and not storage['invulnerabilityOverride']
    ordinary = receipt('docs/porting/th14-natural-current-replay-normal-template-layer-verified-oct14.json',
                       'tools/th14-normal-template-layer-replay-evidence-check.mjs')
    assert ordinary['diagnosticEvidenceVerified'] and ordinary['naturalInputFrames'] == 95220
    assert (ordinary['activeDifferentWords'], ordinary['inactiveScoreDifferentWords']) == (0, 10)

    sanitizer = receipt('docs/porting/th14-sanitized-replay-template-layer-oct14-observed-oct13.json',
                        'tools/th14-sanitized-replay-check.mjs')
    matrix = receipt(MATRIX, 'tools/th14-sanitized-template-layer-matrix-check.mjs')
    assert sanitizer['passed'] and sanitizer['frames'] == 96016 and not sanitizer['errors'] and not sanitizer['gameOver']
    assert sanitizer['sourceHashes'] == matrix['sourceHashes'] == engine['sourceHashes']
    verify('runtimes/th12/th12_web/tests/cpp/th14-public-replay-physical-fixture.cpp', matrix['fixtureSha256'])
    assert sanitizer['fixtureSha256'] == matrix['fixtureSha256']
    assert matrix['sanitizerMatrixVerified'] and len(matrix['cases']) == 3
    assert [(row['frames'], row['stage']) for row in matrix['cases']] == [(90793, 6), (98074, 6), (39458, 7)]
    assert all(row['sanitizerPassed'] and row['candidatePlaybackEnded'] and not row['gameOver'] and not row['errors'] for row in matrix['cases'])
    directory = 'artifacts/th14/sanitized-replay/template-layer-oct14/'
    compile_build = load(directory + 'compile-build.json')
    assert compile_build['sourceHashes'] == engine['sourceHashes'] and len(compile_build['objectSha256']) == 141
    verify(directory + 'compile-build.json', matrix['compileBuildSha256'])
    verify(directory + 'sanitized.mjs', matrix['loaderSha256'])
    verify(directory + 'sanitized.wasm', matrix['wasmSha256'], matrix['wasmBytes'])
    assert sanitizer['wasmSha256'] == matrix['wasmSha256']
    assert '-fsanitize=address,undefined' in matrix['sanitizerFlags'] and '-fno-sanitize-recover=all' in matrix['sanitizerFlags']
    for path, digest in compile_build['objectSha256'].items():
        verify(path, digest)

    browser = receipt('docs/porting/th14-template-layer-browser-flow-verified-oct14.json',
                      'tools/th14-template-layer-browser-flow-evidence-check.mjs')
    assert browser['observedBrowserFlowVerified'] and browser['replayFrames'] == 468
    assert browser['recordedUnderPreviousBuild'] and browser['consoleErrors'] == 0
    assert sum(row['level'] == 'warn' for row in browser['consoleEntries']) == browser['consoleWarnings']
    assert sum(row['level'] == 'error' for row in browser['consoleEntries']) == browser['consoleErrors']
    assert browser['currentConsoleWarnings'] == browser['currentConsoleErrors'] == 0
    assert not any(row['level'] in ('warn', 'error') for row in browser['currentConsoleEntries'])
    sdl = load('runtimes/th14/th14_web/artifacts/sdl3-release/build.json')
    assert browser['build'] == sdl and sdl['bytes'] == 1872163
    assert sdl['sha256'] == 'fe4061f1103e0cd51351e24c11cad4f0cb99e13ae63750262ac3fcfe29bf50e8'
    verify('runtimes/th14/th14_web/artifacts/sdl3-release/th11.wasm', sdl['sha256'], sdl['bytes'])
    assert (len(sdl['sources']), len(sdl['headers'])) == (146, 144)
    for name, digest in {**sdl['sources'], **sdl['headers']}.items():
        verify('runtimes/th12/' + name, digest)
    for name in ('docs/porting/th14-launcher-runtime-prepared-template-layer-oct14.json',
                 'docs/porting/th14-launcher-preview-prepared-template-layer-shell-oct14.json'):
        prepared = receipt(name)
        assert prepared['passed']
    shell = receipt('docs/porting/th14-app-shell-precache-current-verified-oct14.json',
                    'tools/th14-app-shell-precache-current-evidence-check.py', 'verifierSha256')
    assert shell['evidencePassed'] and shell['appShellPolicySatisfied'] and not shell['fullGameOfflineVerified']
    assert shell['runtimeBuildSha256'] == sdl['sha256'] and shell['verifiedSiteFiles'] == 127
    assert (shell['precacheEntries'], shell['precacheBytes'], shell['originalGameResourcesPreserved']) == (97, 4284044, 28)
    assert shell['managedDataPreserved'] and shell['runtimeHtmlJsWasmPreserved'] and shell['hostUiFontAssetsPreserved']
    assert shell['unchangedWorkerSecurityAndLifecycleTemplate'] and shell['generatedWorkerSyntaxPassed']
    assert not shell['currentWarningCauseEstablished']
    for name, row in shell['inventory'].items():
        verify(str(Path(shell['deployment']) / name), row['sha256'], row['bytes'])

    result = dict(diagnosticCheckpointVerified=True, completeGame=False, nativeEquivalent=False,
        sourceFilesVerified=265, sourceHashes=engine['sourceHashes'], cases=cases,
        lunaticNativeCaptureBudget=90793, lunaticNativeCapturedCallbacks=90793, lunaticNativeOrdinaryTerminalVerified=False,
        lunaticEqualGameplayFields=29, lunaticLoadingGameplayDifferences=25, lunaticAbsoluteVisualDifferences=181570,
        lunaticRetainedDetailDifferences=80, lunaticLoadingEnemyNextIdDifferences=72, lunaticActiveAreaZWordDifferences=8,
        lunaticActiveAreaOwnerMetadataDifferences=0,
        originalZConsumerControlCases=48, originalAreaZOutputRemainsObservable=True,
        actualProductionTemplateLayerCallerCases=7, originalTemplateLayerFactoryControlsReused=14,
        frozenClockStoreControls=6, nativeBootstrapClockDirectlyObserved=True,
        clockCampaignSeedOrCounterChanged=False, clockRelevantCurrentSourcesEqualFrozenSnapshots=True,
        historicalImmutableReceipts=historical,
        normalNativeCallbacks=96016, normalEqualGameplayFields=29, normalLoadingGameplayDifferences=25,
        extraNativeCallbacks=39458, extraEqualGameplayFields=30, extraGameplayDifferences=0,
        extraAbsoluteVisualDifferences=78916, ordinaryNaturalInputFrames=95220, ordinaryEndingFrames=3737,
        ordinaryScoreBytes=22379, ordinaryDecodedScoreBytes=149076,
        ordinaryRecordedReplayActiveDifferentWords=0, ordinaryRecordedReplayInactiveScoreDifferentWords=10,
        sanitizerCases=[dict(title='SakuyaA Normal', frames=96016, passed=True), *matrix['cases']],
        browserReplayFrames=468, browserRecordedUnderPreviousBuild=True, browserPersistenceAcrossBuildUpdateObserved=True,
        browserConsoleWarnings=browser['consoleWarnings'], browserConsoleErrors=browser['consoleErrors'],
        browserCurrentLaunchWarnings=browser['currentConsoleWarnings'], browserCurrentLaunchErrors=browser['currentConsoleErrors'],
        appShellPrecacheEntries=97, appShellPrecacheBytes=4284044, originalGameResourcesPreserved=28,
        fullGameOfflineVerified=False, retainedWarningCauseEstablished=False,
        sdl=dict(bytes=sdl['bytes'], sha256=sdl['sha256'], sources=146, headers=144),
        publicEvidenceReceipts=receipts, bindings=bindings, toolSha256=SHA(Path(__file__).read_bytes()),
        scope='Current graze24, player death27/hit28 and bullet cancellation199 preserve original template layers through factory layer -1. Seven actual production caller controls load the original full archive and agree with the independently frozen Native root layer/file/script controls; these controlled API triggers are not ordinary collision/menu or pixel proof. Four intact public inputs finish current production and nonrecovering ASAN/UBSan. Native Lunatic reaches its requested 90,793 capture budget, not a certified ordinary Native terminal. Current 25 loading gameplay-call, 72 loading enemyNextId, 8 active raw area Z and 181,570 absolute visual differences remain unmasked; Extra retains 78,916 absolute visual differences. The original ReimuA path reads an unwritten third polar output word, while the actual stack writers of the 8 captured Z values remain unknown. Existing controlled Z evidence retains observable lastHit output. Six original clock-store controls and a directly observed bootstrap clock are bound to frozen sources, with the relevant current files independently confirmed unchanged; campaign seeds/counters and loading counts are not corrected to match the oracle. Prior hit-effects visual-increment/fanout/checkpoint facts are explicitly immutable historical receipts, not current-source passes. App Shell precaches 97 shell/runtime entries totaling 4,284,044 bytes; all 28 game font/music resources and managed DATA remain deployed. This does not establish warning causality or full-game offline behavior. Current ordinary clear/ending/storage/replay and current browser evidence are separately bound, with every observed warning and inactive score difference retained. All modes, ordinary Native startup/loading, full owner memory, visual RNG, pixels/audio and whole-game 1:1 remain unfinished.')
    (ROOT / OUTPUT).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in ('diagnosticCheckpointVerified', 'sourceFilesVerified',
        'lunaticNativeCapturedCallbacks', 'lunaticRetainedDetailDifferences', 'actualProductionTemplateLayerCallerCases',
        'ordinaryNaturalInputFrames', 'ordinaryScoreBytes', 'browserConsoleWarnings', 'browserConsoleErrors')}))


if __name__ == '__main__':
    main()
