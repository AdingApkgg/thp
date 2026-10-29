"""Check a proposed Scene timing diagnostic without accepting its schedule."""
from pathlib import Path
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda raw: hashlib.sha256(raw).hexdigest()


def evidence():
    home = ROOT / 'artifacts/th14/scene-publish-window-oct30'
    previous = ROOT / 'artifacts/th14/vm-return-worker-oct29'
    bindings = {}

    def read(path):
        raw = path.read_bytes()
        bindings[path.relative_to(ROOT).as_posix()] = dict(bytes=len(raw), sha256=SHA(raw))
        return raw

    def load(path):
        return json.loads(read(path))

    old = previous / 'controlled-prefix33000'
    new = home / 'controlled-next-player-diagnostic'
    baseline = home / 'old-controlled-next-player-diagnostic'
    plan = load(home / 'diagnostic-plan.json')
    assert plan['sceneTimingProposedNotAccepted'] and not plan['strictGatesWeakened']
    assert plan['baseComparatorSha256'] == SHA(read(ROOT / 'tools/th14-compare-native-campaign.mjs'))
    assert plan['diagnosticComparatorSha256'] == SHA(read(home / 'compare-next-player-diagnostic.mjs'))
    before, after, retained = [load(path / 'report.json') for path in (old, new, baseline)]
    assert before['wasmSha256'] == after['wasmSha256'] == '4f9956c748625a71d4e11ea90a1119f5ba9bb7ad100c0bc41cf099e83357ee0f'
    assert all(row['callbacks'] == 33000 and row['allRaw32ByteIdentical'] for row in (before, after, retained))
    assert after['proposedScenePublicationWindowDiagnostic'] and not after['scenePublicationWindowAccepted']
    assert after['scenePublicationWindowDelivery'] == 'existing next observed Player pump'
    assert after['normalVmBoundaryObservation']['modelClock']['delivered'] == 1
    assert retained['normalVmBoundaryObservation']['modelClock']['delivered'] == 0
    assert retained['normalVmReturnBoundaryUnsupported']
    camera = load(old / 'camera-report.json')
    assert not camera['allCameraWordsEqual'] and camera['counts'] == {'12': 17039}
    assert camera['first']['12'] == dict(index=14064, field=12, native=0, portable=3212836864)
    for path in (new, baseline):
        assert load(path / 'camera-report.json')['allCameraWordsEqual']
        assert load(path / 'hud-report.json')['allHudWordsEqual']
        vm = load(path / 'live-report.json')
        assert vm['allLiveValuesEqual'] and sum(row['nativeCount'] for row in vm['snapshots']) == 651
        combat = load(path / 'combat-snapshots.json')
        assert combat['allCapturedCombatWordsEqual'] and len(combat['snapshots']) == 288
        assert all(row['allHandlesFileScriptEqual'] for row in load(path / 'allocation-report.json')['windows'])
    old_names = {p.name for p in old.iterdir() if p.is_file()}
    assert old_names == {p.name for p in new.iterdir() if p.is_file()}
    changed = []
    for name in sorted(old_names):
        if read(old / name) != read(new / name):
            changed.append(name)
    assert changed == ['camera-report.json', 'portable-camera.u32', 'report.json']
    negative = read(home / 'strict-diagnostic-rejection.log')
    assert b'AssertionError: Proposed Scene publication-window timing is diagnostic only' in negative
    assert not (home / 'diagnostic-must-not-be-accepted.json').exists()
    regression = load(home / 'passive-regression-verified.json')
    assert regression['verifiedFiniteEvidence'] and regression['callbacks'] == 33000
    assert regression['allCamera25Equal'] and regression['allSelected32Equal']
    assert regression['vm303Rows'] == 629 and regression['combatCheckpoints'] == 304
    assert regression['verifierSha256'] == SHA(read(ROOT / 'tools/th14-verify-native-campaign.py'))
    return dict(verifiedFiniteProposedSceneTimingDiagnostic=True,
                callbacks=33000, previousMismatchedCameraRows=17039,
                proposedTimingCameraMismatchRows=0, selectedCameraWordsPerRow=25,
                selected32HudVm303AndCombatUnchanged=True,
                unchangedOutputFiles=len(old_names)-len(changed), changedOutputFiles=changed,
                vm303Rows=651, combatCheckpoints=288, initialOrderedPublications=2870,
                sameWasmForBeforeAndAfter=True, gameImplementationChanged=False,
                nativeCameraValuesSuppliedToEngine=False,
                retainedOldCoreAlsoMatchesButCannotDeliverVmReturnClock=True,
                defaultVerifierRejectsProposedSceneTiming=True,
                independentRegressionCallbacks=33000, independentRegressionVmRows=629,
                independentRegressionCombatCheckpoints=304,
                scenePublicationWindowAccepted=False, ordinaryIndependentTimingAccepted=False,
                originalHistoricalCameraFailureClosed=False,
                completeGame=False, nativeEquivalent=False,
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
