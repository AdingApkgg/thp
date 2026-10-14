"""Recompute the full focused-growth retail comparison without hiding failures.

Reads existing captures only. It never launches a game, rewrites inputs, merges
callbacks, or replaces owner-memory differences with selected gameplay equality.
"""
import array
import hashlib
import json
import struct
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = 'docs/porting/th14-continuous-late-native-trace-zps-reimua-lunatic-full-focused-growth-oct14-observed-oct13.json'
OUTPUT = 'docs/porting/th14-focused-growth-full-combat-verified-oct14.json'
BASE = 'artifacts/th14/custom-replay-reference/zps-reimua-lunatic-full-focused-growth-oct14'
SHA = lambda data: hashlib.sha256(data).hexdigest()


def main():
    bindings = {}

    def bind(name):
        path = (ROOT / name).resolve()
        assert path.is_relative_to(ROOT), str(path)
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            while chunk := stream.read(4 * 1024 * 1024):
                digest.update(chunk)
        key = path.relative_to(ROOT).as_posix()
        result = dict(bytes=path.stat().st_size, sha256=digest.hexdigest())
        bindings[key] = result
        return path, result

    def read(name):
        path, binding = bind(name)
        value = path.read_bytes()
        assert SHA(value) == binding['sha256']
        return value

    def load(name):
        return json.loads(read(name))

    def verify(name, expected):
        path, binding = bind(name)
        assert binding['sha256'] == expected, str(path)
        return path

    report = load(REPORT)
    native_path = verify(report['nativeTracePath'], report['nativeTraceSha256'])
    native = load(native_path)
    details = load(verify(report['rawDetailPath'], report['rawDetailSha256']))
    receipt = load(str(native_path).replace('.json', '.compact-receipt.json'))
    assert receipt == report['compactReceipt'] and receipt['allValuesEqual']
    original, source_binding = bind(receipt['source'])
    assert source_binding == dict(bytes=receipt['sourceBytes'], sha256=receipt['sourceSha256'])
    assert bindings[native_path.relative_to(ROOT).as_posix()] == dict(
        bytes=receipt['outputBytes'], sha256=receipt['outputSha256'])
    verify('tools/th14-native-trace-compact.py', receipt['toolSha256'])

    count = len(native['frames'])
    assert count == native['capturedFrames'] == receipt['frames'] == 90793
    assert count == report['comparedFrames'] == report['nativeCaptureCallbackCount'] == len(details)
    assert report['maximumCallbacks'] == count and report['remainingNativeCallbacks'] == 0
    assert report['physicalInvocationOrder'] and report['loadingCallbacksRetained']
    assert report['absentPlayerObservations'] == []
    assert report['lateObservationWindow'] == [15820, 15890]
    assert report['extraProductionObservationWindow'] == [0, 0]
    assert report['terminalPhase'] == 4 and not report['passed']
    assert not native['timedOut'] and native['error'] == '' and native['noInputInjection']
    assert native['rngWrites'] == native['beamFallbacks'] == native['events'] == []
    assert native['childGameStateOverrides'] == 1 and not native['ordinaryMenuLoaderVerified']
    init = native['caseInitialization']
    assert report['nativeCaseInitialization'] == init
    assert (init['address'], init['before'], init['after'], init['wordWrites'], init['replayManagerMode']) == (
        '0x4f58b8', 0x40, 0, 1, 1)
    assert init['afterReadOnlyBootstrap'] and init['beforeFirstPlayerInstruction']
    verify('tools/th14-native-session-capture.py', native['captureToolSha256'])
    verify('tools/th14-native-stored-bootstrap-capture.py', native['warmReplayCaptureToolSha256'])
    observer = native['lateCollisionObserver']
    assert observer == report['lateObserver']
    assert observer['first'] == 15820 and observer['last'] == 15890
    assert observer['combatObservationEnabled'] and not observer['fireObservationEnabled']
    verify('tools/th14-native-first-loader-angle-capture.py', observer['toolSha256'])

    engine = load('runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json')
    assert engine == report['engineBuild'] and len(engine['sourceHashes']) == 265
    rt = 'runtimes/th12/th12_web/'
    for name, digest in engine['sourceHashes'].items():
        verify(rt + name, digest)
    for name, key in (
        ('tools/th14-continuous-late-combat-trace-check.mjs', 'toolSha256'),
        (BASE + '/reference.wasm', 'wasmSha256'),
        (BASE + '/late-combat-fixture.cpp', 'fixtureSha256'),
        (rt + 'tests/cpp/th14-public-replay-physical-fixture.cpp', 'publicFixtureSha256'),
        (rt + 'tests/cpp/th14-custom-replay-reference-fixture.cpp', 'customFixtureSha256'),
        (rt + 'tests/cpp/th14-session-reference-fixture.cpp', 'includedFixtureSha256'),
    ):
        verify(name, report[key])
    manifest_path = 'artifacts/th14/native-campaign-assets/57d84a5cbe82-0f82baec9b33/manifest.json'
    manifest = load(verify(manifest_path, report['archiveManifestSha256']))
    assert manifest['passed'] and manifest['unchangedEntries'] == 226
    assert next(x for x in native['files'] if x['name'] == 'th14.dat')['sha256'] == manifest['referenceArchiveSha256']
    verify(manifest['replayPath'], report['replaySha256'])
    assert report['replaySha256'] == manifest['replaySha256']

    portable_bytes = read(verify(BASE + '/portable-state.u32', report['portableStateSha256']))
    stored_native_bytes = read(verify(BASE + '/native-state.u32', report['nativeStateSha256']))
    assert len(portable_bytes) == len(stored_native_bytes) == count * 32 * 4
    expected_words = array.array('I')
    gameplay, visual, detail_differences = [], [], []
    stage_callbacks, active_callbacks, maxima, windows = Counter(), Counter(), {}, Counter()
    captured_fields, equal_fields, equal_detail_words = Counter(), Counter(), Counter()
    mappings = (
        ('popupWords', 'popupWords', False), ('popupCursor', 'popupCursor', False),
        ('enemies', 'enemyDetails', False), ('phases', 'enemyPhaseDetails', False),
        ('shots', 'liveShots', False), ('items', 'itemDetails', True),
        ('bullets', 'bulletDetails', True), ('damageAreas', 'damageAreas', False),
        ('enemyHitboxAngles', 'enemyHitboxAngles', False), ('enemyIds', 'enemyIds', False),
        ('shotRewards', 'shotRewardCounters', False), ('enemyNextId', 'enemyNextId', False),
    )
    serialized_rows = lambda rows: sorted(json.dumps(row, separators=(',', ':')) for row in rows)

    for index, (row, portable, observed) in enumerate(zip(
            native['frames'], details, struct.iter_unpack('<32I', portable_bytes))):
        assert row['index'] == portable['index'] == index
        stage = row['selection'][3]
        assert row['selection'][:3] == [0, 0, 3]
        assert portable['stage'] == stage == observed[30]
        assert portable['stageFrame'] == row['stageFrame'] == observed[0]
        assert portable['active'] in (0, 1)
        stage_callbacks[stage] += 1
        active_callbacks[portable['active']] += 1
        maxima[stage] = max(maxima.get(stage, 0), row['stageFrame'])
        g, p = row['globals'], row['player']
        expected = [row['stageFrame'], row['held'], row['pressed'], *p[:9],
                    g[2], g[6], g[9], g[12], g[15], g[16], g[18], g[19], g[5],
                    row['scriptRng'][0], row['scriptRng'][2], row['replayRng'][0], row['replayRng'][2],
                    row['enemyCount'], row['shots'], *row['selection'], row['scaleFlags']]
        expected = [value & 0xffffffff for value in expected]
        expected_words.extend(expected)
        for field, (actual, wanted) in enumerate(zip(observed, expected)):
            if actual != wanted:
                target = visual if field in (21, 22) else gameplay
                target.append(dict(index=index, stage=stage, frame=portable['stageFrame'],
                                   field=report['fieldNames'][field], port=actual, native=wanted))
        is_window = 15820 <= row['stageFrame'] <= 15890
        if is_window:
            assert portable['active']
            windows[stage] += 1
        for key, native_key, unordered in mappings:
            if native_key not in row:
                continue
            captured_fields[key] += 1
            a, b = portable[key], row[native_key]
            equal = serialized_rows(a) == serialized_rows(b) if unordered else a == b
            if equal:
                equal_fields[key] += 1
                if isinstance(a, list):
                    equal_detail_words[key] += sum(len(v) if isinstance(v, list) else 1 for v in a)
            else:
                detail_differences.append(dict(index=index, stage=stage, frame=portable['stageFrame'],
                                               kind=key, port=a, native=b))
        if is_window:
            for key in ('enemyDetails', 'enemyPhaseDetails', 'liveShots', 'damageAreas',
                        'enemyHitboxAngles', 'bulletDetails'):
                assert key in row

    if sys.byteorder != 'little':
        expected_words.byteswap()
    assert expected_words.tobytes() == stored_native_bytes
    assert gameplay == report['differences'] and visual == report['startupVisualDifferences']
    assert detail_differences == report['detailDifferences']
    assert len(gameplay) == 25 and len(visual) == 181570 and len(detail_differences) == 99
    assert Counter(x['field'] for x in gameplay) == {'replayCalls': 25}
    assert all(not details[x['index']]['active'] and x['frame'] == 0 for x in gameplay)
    loading = [x for x in detail_differences if not details[x['index']]['active']]
    active = [x for x in detail_differences if details[x['index']]['active']]
    assert len(loading) == 72 and all(x['kind'] == 'enemyNextId' and x['frame'] == 0 for x in loading)
    assert len(active) == 27
    active_column_counts = Counter()
    position_z = []
    for x in active:
        assert x['kind'] == 'damageAreas' and x['stage'] == 5 and 15820 <= x['frame'] <= 15846
        assert len(x['port']) == len(x['native']) == 1
        a, b = x['port'][0], x['native'][0]
        assert len(a) == len(b) == 20
        changed = [index for index, pair in enumerate(zip(a, b)) if pair[0] != pair[1]]
        assert changed in ([18, 19], [8, 18, 19])
        active_column_counts.update(changed)
        if 8 in changed:
            position_z.append(dict(index=x['index'], stage=x['stage'], frame=x['frame'],
                                   port=a[8], native=b[8]))
        assert a[0] == 177 and a[18:] == [0, 0] and b[18:] == [37, 1]
    assert active_column_counts == {8: 8, 18: 27, 19: 27}
    assert [(x['frame'], x['native']) for x in position_z] == [
        *[(frame, 5092616) for frame in range(15828, 15835)], (15835, 366010528)]
    assert windows == {4: 71, 5: 71, 6: 71}
    assert all(maxima[s] < 15820 for s in (1, 2, 3))
    assert active_callbacks == {1: 90043, 0: 750}

    result = dict(
        diagnosticEvidenceVerified=True, comparisonPassed=False, completeGame=False, nativeEquivalent=False,
        sourceFilesVerified=len(engine['sourceHashes']), sourceHashes=engine['sourceHashes'],
        comparedCallbacks=count, rawWords=count * 32,
        stages=dict(stage_callbacks), activeCallbacks=active_callbacks[1], inactiveCallbacks=active_callbacks[0],
        stageMaximumClocks=maxima, lateWindow=[15820, 15890], activeLateWindowCallbacks=dict(windows),
        capturedDetailFields=dict(captured_fields), equalDetailFields=dict(equal_fields),
        equalDetailWords=dict(equal_detail_words), rawGameplayDifferences=len(gameplay),
        rawVisualDifferences=len(visual), retainedDetailDifferences=len(detail_differences),
        inactiveLoadingDetailDifferences=len(loading), activeBattleDetailDifferences=len(active),
        equalSelectedGameplayFields=[name for index, name in enumerate(report['fieldNames'])
                                     if index not in (21, 22, 24)],
        allRawGameplayDifferencesDuringProductionInactiveLoading=True,
        rawGameplayDifferenceRecords=gameplay, detailDifferenceRecords=detail_differences,
        activeAreaDifferenceColumns=[8, 18, 19], activeAreaDifferenceColumnCounts=dict(active_column_counts),
        activeAreaDifferenceMeaning=['position.z raw float word', 'owner shot timer.current', 'owner shot flags'],
        activeAreaPositionZDifferenceRecords=position_z,
        activeAreaDifference= dict(stage=5, slot=177, firstFrame=15820, lastFrame=15846,
                                  portable=[0, 0], native=[37, 1]),
        nativeCaseInitialization=init, nativeCaptureTimedOut=native['timedOut'],
        nativeOrdinaryMenuLoaderVerified=False, allRowsRetained=True, bindings=bindings,
        verifierSha256=SHA(Path(__file__).read_bytes()),
        scope='All90793 continuous callbacks, raw32 words and captured details are independently recomputed in physical order. No clocks are merged, rows removed, visual fields masked, or gameplay values reseeded.29 selected gameplay fields agree throughout;25 gameplay-call differences remain during production inactive loading. The71-frame late window is observed at stages4,5,6; stages1,2,3 never reach15820.72 enemyNextId differences occur during inactive loading.27 ACTIVE stage5 area rows differ in owner timer/flags;8 of those rows also differ in position.z raw float words. These retained differences prevent an all-object equivalence claim despite selected gameplay equality. All99 detail differences and25 raw gameplay differences remain here;181570 visual differences remain in the hash-bound full source report. Native compaction is bound to both exact file hashes and its existing all-values-equal receipt; this verifier does not separately reparse the555MB whitespace source. The declared warm Replay initialization, requested native capture budget and production replay terminal phase remain explicit. No ordinary menu startup, full endings, all owner memory, pixels/audio, storage, all characters/difficulties or whole-game1:1 certification.')
    (ROOT / OUTPUT).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in (
        'diagnosticEvidenceVerified', 'comparisonPassed', 'comparedCallbacks', 'rawGameplayDifferences',
        'rawVisualDifferences', 'retainedDetailDifferences', 'inactiveLoadingDetailDifferences',
        'activeBattleDetailDifferences', 'activeLateWindowCallbacks')}))


if __name__ == '__main__':
    main()
