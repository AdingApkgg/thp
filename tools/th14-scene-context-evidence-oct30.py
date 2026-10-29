"""Verify the bounded stopped-context observation, retaining its strict failures."""
from pathlib import Path
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda raw: hashlib.sha256(raw).hexdigest()


def evidence():
    home = ROOT / 'artifacts/th14/scene-publish-window-oct30'
    native = home / 'context-native'
    bindings = {}

    def read(path):
        raw = path.read_bytes()
        bindings[path.relative_to(ROOT).as_posix()] = dict(bytes=len(raw), sha256=SHA(raw))
        return raw

    def load(path):
        return json.loads(read(path))

    report = load(native / 'report.json')
    plan = load(home / 'context-plan.json')
    prepared = load(home / 'context-observer/prepared.json')
    assert report['callbacks'] == plan['maximumCallbacks'] == 15000
    assert report['childExited'] and not report['error'] and not report['debugErrors']
    assert report['diagnosticStopReason'] == 'maximumCallbacks' and not report['fullReplayAccepted']
    assert report['hardwareBreakpointsOnly'] and report['additionalBreakpointCount'] == 0
    assert report['sceneCopyMainStoppedContext'] and not report['explicitThreadSchedulingControl']
    assert report['instructionBytesPatched'] == report['rngOrCounterWrites'] == 0
    assert report['gameStateWordWrites'] == 1 and report['caseInitialization']['attractBitClearOnly']
    assert report['configuredMusicAndSoundVolumeZero'] and not report['actualAudioPcmMeasured']
    assert report['observerOptions']['maximum_capture_gib'] == plan['maximumCaptureGiB'] == 0.125
    assert report['observerOptions']['minimum_free_gib'] == plan['minimumFreeGiB'] == 100
    assert not plan['automaticNextCase']
    assert report['sourceFullReplaySha256'] == plan['intactReplaySha256']
    source = read(native / 'observer-source.py')
    assert source == read(home / 'context-observer/observer.py')
    assert SHA(source) == report['sourceSha256'] == prepared['generatedObserverSha256'] == plan['observerSha256']
    assert prepared['baseObserverSha256'] == SHA(read(ROOT / prepared['baseObserverPath']))
    assert prepared['preparerSha256'] == SHA(read(ROOT / 'tools/th14-prepare-scene-context-observer-oct30.py'))
    copies = [json.loads(line) for line in read(native / 'scene-camera-copy-events.jsonl').splitlines()]
    assert [row['event'] for row in copies] == ['scene-camera-copy-before', 'scene-camera-copy-after']
    assert [row['pc'] for row in copies] == [0x40d435, 0x40d447]
    assert copies[0]['hostMonotonicNs'] < copies[1]['hostMonotonicNs']
    assert copies[0]['scene'] == copies[1]['scene'] and copies[0]['threadId'] == copies[1]['threadId']
    for row in copies:
        assert row['readOnly'] and row['stage'] == 2 and row['mainPhaseAtObservation'] == 'draw'
        assert row['sampledAfterDebugStopNotSimultaneous']
        assert not row['explicitThreadSchedulingControl'] and not row['nativeValuesProvidedToEngine']
        ctx = row['mainThreadStoppedContext']
        assert len(ctx['registers']) == 11 and len(ctx['debugRegisters']) == 6
        assert 0 < len(bytes.fromhex(ctx['stackHex'])) <= 64
        assert 0 < len(bytes.fromhex(ctx['instructionHex'])) <= 8
        assert ctx['debugRegisters']['dr0'] == 0x44dbd0
    comparisons = []
    for name in ['context-prefix15000', 'old-context-prefix15000']:
        path = home / name
        r = load(path / 'report.json')
        assert r['allRaw32ByteIdentical'] and r['callbacks'] == 15000
        assert load(path / 'camera-report.json')['allCameraWordsEqual']
        assert load(path / 'hud-report.json')['allHudWordsEqual']
        live = load(path / 'live-report.json')
        assert not live['allLiveValuesEqual']
        assert [(s['frame'], s['differenceCount']) for s in live['snapshots']] == [(1, 84), (15000, 82)]
        combat = load(path / 'combat-snapshots.json')
        assert not combat['allCapturedCombatWordsEqual'] and len(combat['differences']) == 2
        assert all(row['family'] == 'shots' and row['field'] == 'animation' for row in combat['differences'])
        first = load(path / 'allocation-report.json')['windows'][0]['firstHandleDifference']
        assert first['index'] == 49 and first['native']['precedingPlayerCallbacks'] == 0
        assert first['native']['poolSlot'] == 8154 and first['portable']['handle'] & 8191 == 8189
        comparisons.append(path)
    payloads = sorted(p.name for p in comparisons[0].iterdir() if p.is_file() and p.name.startswith(('portable-', 'combat-', 'native-')))
    assert len(payloads) == 212
    assert all(read(comparisons[0] / name) == read(comparisons[1] / name) for name in payloads)
    return dict(verifiedFiniteStoppedSceneContextObservation=True, callbacks=15000,
                sceneCopies=1, stoppedMainThreadContexts=2, additionalBreakpoints=0,
                explicitThreadSchedulingControl=False, mainPcNotSimultaneousMemoryReadTime=True,
                oldCrossUpdateCameraWindowReproduced=False, selected32Camera25AndHudEqual=True,
                strictComparisonPassed=False, vmDifferenceCounts=[84, 82], shotHandleDifferences=2,
                firstPublicationHandleDifferenceIndex=49, firstDifferenceBeforeGameplay=True,
                oldAndNewCorePayloadsIdentical=212, nativeCameraValuesSuppliedToEngine=False,
                historicalFailuresClosed=False, completeGame=False, nativeEquivalent=False,
                verifierSha256=SHA(Path(__file__).read_bytes()), bindings=bindings)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(ROOT / 'artifacts/th14') or output.is_relative_to(ROOT / 'docs/porting')
    result = evidence()
    if args.check:
        assert json.loads(output.read_bytes()) == result
    else:
        output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'bindings'}))


if __name__ == '__main__':
    main()
