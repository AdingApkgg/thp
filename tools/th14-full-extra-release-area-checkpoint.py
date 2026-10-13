"""Bind the current TH14 focused-shot area-release checkpoint without promoting failures."""
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
        ('zps-normal-release-area-oct14','SakuyaA Normal',96016,6,True),
        ('zps-reimub-lunatic-release-area-oct14','ReimuB Lunatic',98074,6,True),
        ('zps-reimua-lunatic-release-area-oct14','ReimuA Lunatic',57373,5,False),
        ('zps-reimua-extra-release-area-oct14','ReimuA Extra',39458,7,True)]:
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
    continuous = read('docs/porting/th14-zps-continuous-retail-release-area-observed-oct14.json')
    assert not continuous['passed'] and continuous['comparedCallbacks'] == 96016
    assert continuous['gameplayDifferences'] == 25 and len(continuous['equalSelectedGameplayFields']) == 29
    objects = read('docs/porting/th14-normal-continuous-object-release-area-failure-receipt-oct14.json')
    assert objects['differencesCount'] == 25 and objects['detailDifferencesCount'] == 70
    assert objects['detailDifferencesKinds'] == {'enemyNextId':70}
    assert not objects['passed'] and objects['fullFailedReportRetained']
    sanitizer = read('docs/porting/th14-sanitized-replay-release-area-oct14-observed-oct13.json')
    assert sanitizer['passed'] and sanitizer['frames'] == 96016 and not sanitizer['errors']
    assert sanitizer['sourceHashes'] == engine['sourceHashes']
    extra = read('docs/porting/th14-extra-continuous-retail-release-area-observed-oct14.json')
    assert extra['passed'] and extra['comparedCallbacks'] == 39458 and extra['gameplayDifferences'] == 0
    assert len(extra['equalSelectedGameplayFields']) == 30
    all_areas = read('docs/porting/th14-physical-replay-native-trace-zps-reimua-extra-full-all-captured-areas-release-oct14-observed-oct13.json')
    assert all_areas['passed'] and all_areas['comparedFrames'] == 39458
    assert not all_areas['differences'] and not all_areas['detailDifferences']
    assert all_areas['engineBuild']['sourceHashes'] == engine['sourceHashes']
    assert 'damageAreas' in all_areas['checkedDetailKinds']
    matrix = read('docs/porting/th14-sanitized-input-parity-matrix-release-area-oct14-observed-oct14.json')
    assert matrix['sanitizerMatrixVerified'] and matrix['sourceHashes'] == engine['sourceHashes']
    assert all(case['sanitizerPassed'] and not case['errors'] for case in matrix['cases'])
    storage = read('docs/porting/th14-natural-storage-normal-sakuyaa-release-area-oct14-verified-oct14.json')
    assert storage['passed'] and storage['naturalInputFrames'] == 95220
    assert storage['clearCount'] == storage['noContinueClearCount'] == 1
    replay = read('docs/porting/th14-natural-current-replay-normal-release-area-verified-oct14.json')
    assert replay['diagnosticEvidenceVerified'] and replay['activeDifferentWords'] == 0
    assert replay['inactiveScoreDifferentWords'] == 10
    sdl = read('runtimes/th14/th14_web/artifacts/sdl3-release/build.json')
    assert SHA(bind('runtimes/th14/th14_web/artifacts/sdl3-release/th11.wasm')) == sdl['sha256']
    for name, digest in {**sdl['sources'], **sdl['headers']}.items():
        assert SHA((ROOT/'runtimes/th12'/name).read_bytes()) == digest, name
    stage2 = read('docs/porting/th14-reimua-lunatic-stage2-release-area-verified-oct14.json')
    assert stage2['passed'] and stage2['comparedFrames'] == 12029
    result = dict(diagnosticCheckpointVerified=True, completeGame=False, nativeEquivalent=False,
        sourceFilesVerified=len(engine['sourceHashes']), sourceHashes=engine['sourceHashes'], cases=cases,
        continuousGameplayDifferences=25, equalSelectedGameplayFields=29,
        continuousObjectDifferences={'enemyNextId':70}, extraRetailCallbacks=39458, extraGameplayDifferences=0, extraVisualDifferences=78916,
        extraCheckedDetailKinds=all_areas['checkedDetailKinds'], naturalNormalInputFrames=95220,
        naturalScoreEncodedBytes=storage['scoreBytes'], naturalReplayInactiveScoreDifferences=10, sanitizerFrames=96016,
        sdl=dict(bytes=sdl['bytes'],sha256=sdl['sha256'],sources=len(sdl['sources']),headers=len(sdl['headers'])),
        sanitizerMatrix=matrix['cases'], bindings=bindings, toolSha256=SHA(Path(__file__).read_bytes()),
        scope='Current production C++ and SDL source hashes, actual independent-retail comparison receipts and intact public-input playback outcomes are bound together. ReimuA target retirement, shared enemy orientation, phase-modulo6 graze reward and rotated enemy-body collision are fixed. The39458-frame uninterrupted Extra warm case has30 selected gameplay fields equal throughout and all captured detailed fields checked by the producer;78916 visual RNG differences remain. ReimuA focused-shot termination now clears its retained area pointer; the complete12029-frame native stage2 case passes, while uninterrupted candidate Lunatic reaches stage5 and GameOver at57373. Standalone stage5 prefix6000 passes; continuous-native transition work remains separate. Normal natural input, ending/results/replay-save and the original score codec are reverified; browser persistent storage and whole native ending remain separate. Normal continuous loading RNG25 and manager-ID70 differences, visual RNG differences, ordinary native menu/ending, full graphics/audio/storage and all-mode whole-game1:1 remain unresolved. No failed result is promoted to a pass.')
    (ROOT/'docs/porting/th14-full-extra-release-area-current-checkpoint-oct14.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(diagnosticCheckpointVerified=True,cases=cases,sdl=result['sdl'])))


if __name__ == '__main__':
    main()
