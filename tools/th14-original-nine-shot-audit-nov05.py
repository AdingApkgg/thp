"""Locate all nine retained original count differences in reproduced models.

No original A VM snapshots are invented. Equality to selected original fields
does not prove equality of the previously unrecorded original VM geometry.
"""
from collections import Counter, defaultdict
from pathlib import Path
import hashlib
import json
import struct

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/original-nine-shot-model-nov05'
SHA = lambda data: hashlib.sha256(data).hexdigest()


def main():
    bindings = {}

    def raw(path):
        data = path.read_bytes()
        bindings[path.relative_to(R).as_posix()] = dict(bytes=len(data), sha256=SHA(data))
        return data

    def load(path):
        return json.loads(raw(path))

    for case in ['off', 'on']:
        result = load(H / 'retry1' / case / 'result.json')
        assert result['driverExitCode'] == result['rawVerifierExitCode'] == 0
        assert result['allExistingPayloadsByteIdentical'] and result['payloadFiles'] == 359
        assert SHA(raw(H / 'retry1' / case / 'driver.mjs')) == result['driverSha256']
        assert load(H / 'retry1' / case / 'raw-verified.json')['verifiedFiniteEvidence']
    pair = load(R / 'artifacts/th14/original-pair-audit-nov05/report.json')
    assert pair['fieldDifferenceCounts'] == {'21': 34428, '22': 34429, '26': 9}
    homes = dict(A=H / 'retry1/on/model', B=R / 'artifacts/th14/shot-lifetime-nov05/baseline/model')
    originals = dict(A=R / 'artifacts/th14/script-rng-read-generation-nov05/prefix-player-pump/native',
                     B=R / 'artifacts/th14/supervisor-pass-rng-nov05/prefix-fixed-startup-retry1/native')
    snapshots = {}
    for name, home in homes.items():
        selected_name = 'selected-state.u32' if name == 'A' else 'diagnostic-state.u32'
        data = raw(home / selected_name)
        assert data == raw(originals[name] / 'selected-state.u32')
        report = load(originals[name] / 'report.json')
        assert SHA(data) == report['selectedSha256'] and report['callbacks'] == 35000
        assert report['childExited'] and not report['error'] and not report['debugErrors']
        selected = list(struct.iter_unpack('<32I', data))
        index = load(home / 'shot-lifetime-index.json')['snapshots']
        assert len(index) == 55
        rows = {}
        for item in index:
            blob = raw(home / item['file'])
            assert SHA(blob) == item['sha256'] and len(blob) == 256*96*4
            key = item['stage'], item['stageFrame']
            values = list(struct.iter_unpack('<96I', blob))
            state = selected[item['callback']-1]
            assert (state[30], state[0]) == key
            assert sum(bool(row[1]) for row in values) == state[26]
            assert key not in rows
            rows[key] = values
        snapshots[name] = rows
    assert snapshots['A'].keys() == snapshots['B'].keys()
    family = lambda frame, row: (frame-row[5], *row[19:25])
    identity = lambda frame, row: (*family(frame, row), *row[12:19])
    flt = lambda value: struct.unpack('<f', struct.pack('<I', value))[0]
    events = []
    for stage, frame in sorted(snapshots['A']):
        current = [snapshots[name][stage, frame] for name in ['A', 'B']]
        counts = [sum(bool(row[1]) for row in rows) for rows in current]
        if counts[0] == counts[1]:
            continue
        original = next(row for row in pair['activeShotDifferences']
                        if (row['stage'], row['stageFrame']) == (stage, frame))
        assert counts == [original['countA'], original['countB']]
        group_counts = [Counter(family(frame, row) for row in rows if row[1]) for rows in current]
        differing_groups = [key for key in group_counts[0].keys() | group_counts[1].keys()
                            if group_counts[0][key] != group_counts[1][key]]
        assert len(differing_groups) == 1
        group = differing_groups[0]
        # Multiple projectiles can share a family and birth frame. Only the
        # full motion key below establishes uniqueness at this boundary.
        assert abs(group_counts[0][group]-group_counts[1][group]) == 1
        previous = [snapshots[name][stage, frame-1] for name in ['A', 'B']]
        lookups = [defaultdict(list), defaultdict(list)]
        for lookup, rows in zip(lookups, previous):
            for row in rows:
                if row[1]:
                    lookup[identity(frame-1, row)].append(row)
        causes = []
        for key in lookups[0].keys() & lookups[1].keys():
            if len(lookups[0][key]) != 1 or len(lookups[1][key]) != 1:
                continue
            rows = [lookup[key][0] for lookup in lookups]
            after = [pool[row[0]] for pool, row in zip(current, rows)]
            retired = [not (new[1] and new[2] == old[2]) for old, new in zip(rows, after)]
            if retired[0] == retired[1]:
                continue
            assert key[:7] == group
            x, y = rows
            assert x[1] == y[1] == 2 and x[25] == y[25] == 1
            assert x[27:29] == y[27:29] == (9, 6)
            assert x[37:39] == y[37:39] == (29, 1)
            assert x[40:49] == y[40:49] and x[50:58] == y[50:58]
            assert x[49] != y[49] and x[84] != y[84]
            for old, new, gone, name in zip(rows, after, retired, ['A', 'B']):
                assert old[66] == 1 and old[5] >= 10 and old[67] == int(not gone)
                assert abs(flt(old[49]) - (flt(old[18])+flt(old[84]))) < 2e-7
                max_y = max(flt(old[i]) for i in [69, 72, 75, 78])
                assert (max_y < 16) if gone else (max_y > 16)
                if not gone:
                    assert new[1] == 2 and new[25] == 1 and new[67] == 0
                    following = snapshots[name][stage, frame+1][old[0]]
                    assert not following[1] or following[2] != old[2]
            causes.append(dict(stage=stage, stageFrame=frame, previousStageFrame=frame-1,
                               slots=[row[0] for row in rows], birthFrame=key[0],
                               countA=counts[0], countB=counts[1], retired=retired,
                               familyBirthMultiplicity=[counter[group] for counter in group_counts],
                               sameUniqueBirthFamilyAndMotion=True,
                               sameDimensionsScaleAndPosition=True,
                               differentRotationAndFloat0=True,
                               rotationEqualsShotAnglePlusFloat0=True,
                               visibilityExactlyPredictsRetirement=True,
                               bothAnimationVmsPresent=True,
                               retainedShotRetiresNextPlayer=True,
                               animationFile=9, animationScript=6,
                               originalGameplayVmGeometryObserved=False))
        assert len(causes) == 1
        events.extend(causes)
    assert len(events) == 9
    assert [(r['stage'], r['stageFrame']) for r in events] == [
        (r['stage'], r['stageFrame']) for r in pair['activeShotDifferences']]
    result = dict(schema='th14/original-nine-shot-model/1', verifiedModelExplanation=True,
                  callbacksPerTrajectory=35000, snapshotPairs=55,
                  originalUniqueStageFramePairs=34429, matchedOldCountDifferenceFrames=9,
                  events=events, allExistingAPayloadsByteIdentical=359,
                  bothModelSelectedStatesExactlyMatchTheirRetainedOriginal=True,
                  modelMechanismExplainsAllNineSelectedCountDifferences=True,
                  oldOriginalAVmGeometryMeasured=False, ordinaryOriginalGuiAccepted=False,
                  independentlyScheduled=False, originalNineDifferencesClosed=False,
                  productionChanged=False, completeGame=False, nativeEquivalent=False,
                  evidenceBindings=bindings, toolSha256=SHA(Path(__file__).read_bytes()))
    (H / 'model-audit.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: result[key] for key in ['verifiedModelExplanation',
        'snapshotPairs', 'matchedOldCountDifferenceFrames', 'oldOriginalAVmGeometryMeasured',
        'originalNineDifferencesClosed', 'completeGame']}))


if __name__ == '__main__':
    main()
