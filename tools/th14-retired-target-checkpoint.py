"""Bind the current TH14 target-retirement checkpoint without promoting its failures."""
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RT = ROOT/'runtimes/th12/th12_web'
SHA = lambda data: hashlib.sha256(data).hexdigest()


def main():
    bindings = {}
    def bind(path):
        path = ROOT/path
        data = path.read_bytes()
        bindings[path.relative_to(ROOT).as_posix()] = dict(bytes=len(data), sha256=SHA(data))
        return data
    def read(path):
        return json.loads(bind(path))
    engine = read('runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json')
    for name, digest in engine['sourceHashes'].items():
        assert SHA((RT/name).read_bytes()) == digest, name
    cases = []
    for label, title, frames, stage, ended in [
        ('zps-normal-retired-target-oct14','SakuyaA Normal',96016,6,True),
        ('zps-reimub-lunatic-retired-target-oct14','ReimuB Lunatic',98074,6,True),
        ('zps-reimua-lunatic-retired-target-oct14','ReimuA Lunatic',20835,2,False),
        ('zps-reimua-extra-retired-target-oct14','ReimuA Extra',17251,7,False)]:
        directory = 'artifacts/th14/public-replay-playback/'+label
        report = read(directory+'/report.json')
        assert report['sourceHashes'] == engine['sourceHashes']
        assert (report['frames'],report['stage'],report['candidatePlaybackEnded']) == (frames,stage,ended)
        assert report['error'] == '' and report['gameOverRequested'] == (not ended)
        assert not report['skipped'] and not report['unsupported']
        assert report['physicalInvocationOrder'] and report['transitionCallbacksRetained']
        assert not report['invulnerabilityOverride'] and not report['forcedProgression']
        assert SHA(bind(directory+'/selected-state.u32')) == report['selectedStateSha256']
        assert SHA(bind(directory+'/callback-active.u8')) == report['callbackActiveSha256']
        assert SHA(bind(directory+'/public-replay.wasm')) == report['wasmSha256']
        cases.append(dict(title=title, frames=frames, stage=stage, candidatePlaybackEnded=ended,
                          gameOver=not ended, nativeEquivalent=False, replaySha256=report['replaySha256']))
    continuous = read('docs/porting/th14-zps-continuous-retail-retired-target-observed-oct14.json')
    assert not continuous['passed'] and continuous['comparedCallbacks'] == 96016
    assert continuous['gameplayDifferences'] == 25 and len(continuous['equalSelectedGameplayFields']) == 29
    objects = read('docs/porting/th14-normal-continuous-object-retired-target-failure-receipt-oct14.json')
    assert objects['differencesCount'] == 25 and objects['detailDifferencesCount'] == 70
    assert objects['detailDifferencesKinds'] == {'enemyNextId':70}
    assert not objects['passed'] and objects['fullFailedReportRetained']
    sanitizer = read('docs/porting/th14-sanitized-replay-retired-target-oct14-observed-oct13.json')
    assert sanitizer['passed'] and sanitizer['frames'] == 96016 and not sanitizer['errors']
    assert sanitizer['sourceHashes'] == engine['sourceHashes']
    focused = read('docs/porting/th14-shot-focused-retired-verified-oct14.json')
    assert focused['passed'] and focused['updates'] == 2304
    retail = read('docs/porting/th14-reimua-retired-target-verified-oct14.json')
    assert retail['diagnosticEvidenceVerified'] and len(retail['results']) == 2
    browser = read('docs/porting/th14-retired-target-browser-flow-verified-oct14.json')
    assert browser['observedBrowserFlowVerified'] and browser['filesVerified'] == 127
    sdl = read('runtimes/th14/th14_web/artifacts/sdl3-release/build.json')
    assert sdl['sha256'] == browser['build']['sha256']
    assert SHA(bind('runtimes/th14/th14_web/artifacts/sdl3-release/th11.wasm')) == sdl['sha256']
    for name, digest in {**sdl['sources'], **sdl['headers']}.items():
        assert SHA((ROOT/'runtimes/th12'/name).read_bytes()) == digest, name
    result = dict(diagnosticCheckpointVerified=True, completeGame=False, nativeEquivalent=False,
        sourceFilesVerified=len(engine['sourceHashes']), sourceHashes=engine['sourceHashes'], cases=cases,
        continuousGameplayDifferences=25, equalSelectedGameplayFields=29,
        continuousObjectDifferences={'enemyNextId':70}, focusedRetirementNativeUpdates=2304,
        extraRetailPrefix=retail['results'], sanitizerFrames=96016,
        sdl=dict(bytes=sdl['bytes'],sha256=sdl['sha256'],sources=len(sdl['sources']),headers=len(sdl['headers'])),
        browserFlowVerified=True, bindings=bindings, toolSha256=SHA(Path(__file__).read_bytes()),
        scope='Current production C++ and SDL source hashes, actual independent-retail comparison receipts and intact public-input playback outcomes are bound together. ReimuA retirement timing is fixed; only the6000-frame Extra prefix and the3450-frame late-detail case are verified against retail. ReimuA Lunatic/Extra still GameOver later. Normal continuous loading RNG25 and manager-ID70 differences, visual RNG differences, ordinary native menu/ending, full graphics/audio/storage and all-mode whole-game1:1 remain unresolved. No failed result is promoted to a pass.')
    (ROOT/'docs/porting/th14-retired-target-current-checkpoint-oct14.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(diagnosticCheckpointVerified=True,cases=cases,sdl=result['sdl'])))


if __name__ == '__main__':
    main()
