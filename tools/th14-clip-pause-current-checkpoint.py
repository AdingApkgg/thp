"""Bind a current SDL graphics/pause checkpoint to the unchanged tested core.

This verifies prior evidence bytes, distinguishes the changed SDL files, and
requires fresh source-bound graphics and browser receipts. It does not rerun
or promote a historical renderer, infer a Native terminal, or hide failures.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIOR = 'docs/porting/th14-template-layer-current-checkpoint-oct14.json'
OUTPUT = 'docs/porting/th14-clip-pause-current-checkpoint-oct14.json'
CHANGED = {
    'runtimes/th12/th12_web/cpp/sdl/Application.cpp',
    'runtimes/th12/portable/sdl/Renderer.cpp',
    'runtimes/th12/portable/sdl/Shaders.hpp',
    'runtimes/th14/th14_web/artifacts/sdl3-release/build.json',
    'runtimes/th14/th14_web/artifacts/sdl3-release/th11.wasm',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--graphics-report', required=True)
    args = parser.parse_args()
    bindings = {}

    def bind(name, expected=None):
        path = (ROOT / name).resolve()
        assert path.is_relative_to(ROOT), path
        key = path.relative_to(ROOT).as_posix()
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        row = {'bytes': path.stat().st_size, 'sha256': digest}
        if expected is not None:
            assert row == expected, key
        if key in bindings:
            assert bindings[key] == row, key
        bindings[key] = row
        return key

    def load(name):
        key = bind(name)
        return json.loads((ROOT / key).read_text(encoding='utf-8'))

    def verify(name, digest):
        key = bind(name)
        assert bindings[key]['sha256'] == digest, key

    prior = load(PRIOR)
    assert prior['diagnosticCheckpointVerified'] and not prior['completeGame']
    assert not prior['nativeEquivalent'] and prior['sourceFilesVerified'] == 265
    historical_sdl_changes = {}
    for name, old in prior['bindings'].items():
        if name in CHANGED:
            key = bind(name)
            assert bindings[key] != old, name
            historical_sdl_changes[name] = {'prior': old, 'current': bindings[key]}
        else:
            bind(name, old)
    assert set(historical_sdl_changes) == CHANGED
    for name, digest in prior['sourceHashes'].items():
        verify('runtimes/th12/th12_web/' + name, digest)

    build = load('runtimes/th14/th14_web/artifacts/sdl3-release/build.json')
    assert build['title'] == 14 and build['releaseProfile'] and not build['completeGame']
    assert (len(build['sources']), len(build['headers'])) == (146, 145)
    for group in ('sources', 'headers'):
        for name, digest in build[group].items():
            verify('runtimes/th12/' + name, digest)
    verify('runtimes/th14/th14_web/artifacts/sdl3-release/th11.wasm', build['sha256'])
    verify('runtimes/th14/th14_web/artifacts/sdl3-release/th11.mjs', build['loaderSha256'])
    assert not any(row['name'].startswith('th11_probe_') or row['name'] in
                   ('th11_tick', 'th11_audio_probe', 'th11_audio_samples') for row in build['exports'])

    graphics = load(args.graphics_report)
    assert graphics['diagnosticEvidenceVerified'] and not graphics['completeGame']
    assert not graphics['nativeEquivalent']
    assert graphics['currentProductionSourceVerified']
    assert graphics['actualColorRendererAndShaderFileBytesEqualCurrentProduction']
    assert graphics['actualUVRendererFileBytesEqualCurrentProduction']
    assert graphics['actualUVShaderDiffersOnlyFragmentOutput']
    assert not graphics['oldGuardShaderBindingReusedAsCurrent']
    verify('tools/th14-stage-production-clip-current-source-evidence-check.py', graphics['toolSha256'])
    for name, row in graphics['sourceBindings'].items():
        bind(name, row)
    evidence = graphics.get('evidence', {})
    entries = evidence.items() if isinstance(evidence, dict) else ((row['path'], row) for row in evidence)
    for name, row in entries:
        bind(name, {'bytes': row['bytes'], 'sha256': row['sha256']})
    pause = load('docs/porting/th14-pause-dialogue-capture-verified-oct14.json')
    assert pause['pauseDialogueCaptureEvidencePassed'] and pause['productionChanged']
    assert pause['sourceHashes'] == prior['sourceHashes']
    for name, digest in pause['productionSourceHashes'].items():
        verify('runtimes/th12/th12_web/' + name, digest)
    for key, hash_key in (('fixture', 'fixtureSha256'), ('wasm', 'wasmSha256'),
                          ('nativeReport', 'nativeReportSha256')):
        verify(pause['paths'][key], pause[hash_key])
    assert len(pause['selectorCases']) == 6 and len(pause['actualDialogueLifecycle']) == 3

    browser_name = 'docs/porting/th14-clip-pause-browser-flow-verified-oct14.json'
    browser = load(browser_name)
    assert browser['observedBrowserFlowVerified'] and browser['build'] == build
    assert browser['replayFrames'] == 468 and browser['recordedUnderPreviousBuild']
    assert browser['currentConsoleErrors'] == browser['currentConsoleWarnings'] == 0
    verify('tools/th14-clip-pause-browser-flow-evidence-check.mjs', browser['toolSha256'])
    for name, row in browser['bindings'].items():
        bind(name, row)
    shell = load('docs/porting/th14-app-shell-precache-clip-pause-verified-oct14.json')
    assert shell['appShellPolicySatisfied'] and shell['precacheBytes'] < 5 * 1024 * 1024

    retained = {k: prior[k] for k in ('cases', 'sanitizerCases',
        'lunaticNativeCapturedCallbacks', 'lunaticNativeOrdinaryTerminalVerified',
        'lunaticEqualGameplayFields', 'lunaticLoadingGameplayDifferences',
        'lunaticAbsoluteVisualDifferences', 'lunaticLoadingEnemyNextIdDifferences',
        'lunaticActiveAreaZWordDifferences', 'normalNativeCallbacks',
        'normalLoadingGameplayDifferences', 'extraNativeCallbacks',
        'extraGameplayDifferences', 'extraAbsoluteVisualDifferences',
        'ordinaryNaturalInputFrames', 'ordinaryEndingFrames',
        'ordinaryRecordedReplayActiveDifferentWords', 'ordinaryRecordedReplayInactiveScoreDifferentWords')}
    report = {'diagnosticCheckpointVerified': True, 'completeGame': False,
        'nativeEquivalent': False, 'unchangedCoreSourceFilesVerified': 265,
        'sourceHashes': prior['sourceHashes'], 'unchangedCoreEvidence': retained,
        'coreLongRunsRepeated': False, 'priorEvidenceBindingsVerifiedUnchanged': 703,
        'historicalSdlChanges': historical_sdl_changes,
        'sdl': {'bytes': build['bytes'], 'sha256': build['sha256'], 'sources': 146, 'headers': 145},
        'graphicsReport': args.graphics_report, 'graphicsColor': graphics['color'],
        'graphicsUV': graphics['uv'], 'pauseSelectorCases': 6,
        'actualDialogueLifecycleCases': 3, 'browserReplayFrames': 468,
        'browserRecordedUnderPreviousBuild': True,
        'browserCurrentLaunchWarnings': 0, 'browserCurrentLaunchErrors': 0,
        'appShellPrecacheBytes': shell['precacheBytes'], 'bindings': bindings,
        'toolSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'scope': 'Current TH14 SDL source and fresh actual production graphics/menu playback evidence. All265 game-core files and703 immutable prior evidence bindings remain byte-identical; the four complete headless/sanitized input and ordinary ending/storage/replay receipts are reused only within that unchanged core scope. Five changed historical SDL bindings are explicitly separated; no prior renderer pass is inherited. Pause correction establishes ordinary active-dialogue source identity/RECT and actual MSG lifetime; DeferredEnd timing/pixels remain unverified. Graphics failures remain in full, and saved468-frame input predates this build. Ordinary Native full ending, staged loader lifecycle/timing, all modes, full browser storage/offline, complete image/audio equality and whole-game1:1 remain unfinished.'}
    (ROOT / OUTPUT).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'diagnosticCheckpointVerified': True, 'bindings': len(bindings), 'sdl': report['sdl']}))


if __name__ == '__main__':
    main()
