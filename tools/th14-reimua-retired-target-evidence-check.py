"""Independently recompute the retained-target retail comparison receipts."""
import hashlib, json, struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RT = ROOT / 'runtimes/th12/th12_web'
SHA = lambda data: hashlib.sha256(data).hexdigest()


def main():
    bindings = {}
    def read(path):
        path = ROOT / path
        data = path.read_bytes()
        bindings[path.relative_to(ROOT).as_posix()] = dict(bytes=len(data), sha256=SHA(data))
        return data
    def load(path):
        return json.loads(read(path))
    results = []
    for label, expected_count in [('zps-reimua-extra-retired-target-oct14', 6000),
                                  ('zps-reimua-extra-combat-raw-retired-target-oct14', 3450)]:
        report = load('docs/porting/th14-' + ('natural' if expected_count == 6000 else 'physical') +
                      '-replay-native-trace-' + label + '-observed-oct13.json')
        native_bytes = read(report['nativeTracePath'])
        assert SHA(native_bytes) == report['nativeTraceSha256']
        native = json.loads(native_bytes)
        assert native['error'] == '' and not native['timedOut'] and native['noInputInjection']
        assert native['childGameStateOverrides'] == 1 and not native['ordinaryMenuLoaderVerified']
        init = native['caseInitialization']
        assert (init['before'], init['after'], init['wordWrites']) == (0x40, 0, 1)
        assert init['afterReadOnlyBootstrap'] and init['beforeFirstPlayerInstruction']
        assert SHA(read('tools/th14-native-stored-bootstrap-capture.py')) == native['warmReplayCaptureToolSha256']
        assert native['executableSha256'] == 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
        assert native['capturedFrames'] == report['comparedFrames'] == expected_count
        assert report['passed'] and not report['differences'] and not report['detailDifferences']
        assert not report['completeGame'] and not report['nativeEquivalent']
        for name, digest in report['engineBuild']['sourceHashes'].items():
            assert SHA(read(RT.relative_to(ROOT) / name)) == digest, name
        directory = 'artifacts/th14/custom-replay-reference/' + label
        raw = read(directory + '/portable-state.u32')
        assert SHA(raw) == report['portableStateSha256']
        actual = list(struct.iter_unpack('<32I', raw))
        assert len(actual) == expected_count
        visual_differences = 0
        for index, (row, words) in enumerate(zip(native['frames'], actual)):
            assert row['index'] == index and row['selection'] == [0, 0, 4, 7]
            g, p = row['globals'], row['player']
            values = [row['stageFrame'], row['held'], row['pressed'], *p[:9],
                      g[2], g[6], g[9], g[12], g[15], g[16], g[18], g[19], g[5],
                      row['scriptRng'][0], row['scriptRng'][2], row['replayRng'][0], row['replayRng'][2],
                      row['enemyCount'], row['shots'], *row['selection'], row['scaleFlags']]
            for field, (value, target) in enumerate(zip(words, values)):
                if value == target & 0xffffffff:
                    continue
                if field in (21, 22):
                    visual_differences += 1
                else:
                    raise AssertionError((index, field, value, target))
        assert visual_differences == len(report['startupVisualDifferences'])
        assert SHA(read(directory + '/reference.wasm')) == report['wasmSha256']
        detail_rows, detail_fields = 0, 0
        if expected_count == 3450:
            assert report['physicalInvocationOrder'] and not report['absentPlayerObservations']
            tool = 'tools/th14-extra-late-combat-raw-trace-check.mjs'
            fixture = 'tests/cpp/th14-extra-late-combat-reference-fixture.cpp'
            raw_details = read(report['rawDetailPath'])
            assert SHA(raw_details) == report['rawDetailSha256']
            details = json.loads(raw_details)
            assert len(details) == expected_count
            fields = {'popupWords': 'popupWords', 'enemyDetails': 'enemies',
                      'enemyPhaseDetails': 'phases', 'liveShots': 'shots',
                      'itemDetails': 'items', 'bulletDetails': 'bullets',
                      'enemyIds': 'enemyIds', 'shotRewardCounters': 'shotRewards',
                      'damageAreas': 'damageAreas', 'popupCursor': 'popupCursor',
                      'enemyNextId': 'enemyNextId'}
            for index, (row, observed) in enumerate(zip(native['frames'], details)):
                assert observed['index'] == index and observed['stageFrame'] == row['stageFrame']
                detail_rows += 1
                for name, key in fields.items():
                    if name not in row:
                        continue
                    a, b = observed[key], row[name]
                    if key in ('items', 'bullets'):
                        a, b = sorted(a), sorted(b)
                    assert a == b, (index, key)
                    detail_fields += 1
            observer = 'tools/th14-native-first-loader-late-collision-capture.py'
            assert SHA(read(observer)) == native['lateCollisionObserver']['toolSha256']
        else:
            tool = 'tools/th14-natural-replay-reference-trace-check.mjs'
            fixture = 'tests/cpp/th14-custom-replay-reference-fixture.cpp'
        assert SHA(read(tool)) == report['toolSha256']
        assert SHA(read(RT.relative_to(ROOT) / fixture)) == report['fixtureSha256']
        results.append(dict(label=label, callbacks=expected_count, rawWords=expected_count*32,
                            gameplayDifferences=0, visualDifferences=visual_differences,
                            independentlyRecomputedDetailRows=detail_rows,
                            independentlyRecomputedDetailFields=detail_fields))
    output = ROOT / 'docs/porting/th14-reimua-retired-target-verified-oct14.json'
    output.write_text(json.dumps(dict(diagnosticEvidenceVerified=True, completeGame=False,
        nativeEquivalent=False, results=results, bindings=bindings,
        verifierSha256=SHA(Path(__file__).read_bytes()),
        scope='All raw32 state words for two independent retail first-loader warm cases; gameplay differences are zero and visual RNG differences remain explicitly counted. The3450 physical-callback case also independently recomputes every captured detailed field, including all popup/ID/reward rows and the3290..3425 enemy/shot/damage/bullet window. Original gameplay runs in the owned retail process; one declared40->0 mode initialization remains. This is not a full Extra clear, ordinary menu/ending, graphics/audio/storage or whole-game1:1 proof.'), indent=2)+'\n')
    print(json.dumps(results))


if __name__ == '__main__':
    main()
