"""Recompute current production raw32 and full-object evidence without masking.

Immutable Native traces are read, never launched.  Every mismatch is retained in
new private files; evidence validity is separate from gameplay equivalence.
"""
import array
import gc
import hashlib
import json
import struct
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RT = ROOT / 'runtimes/th12/th12_web'
HOME = ROOT / 'artifacts/th14/staged-loader-production-playback'
OUT = ROOT / 'artifacts/th14/staged-loader-production-raw-evidence-oct14'
DOC = ROOT / 'docs/porting/th14-staged-loader-production-raw-evidence-verified-oct14.json'
FIELDS = ['stageFrame', 'held', 'pressed', 'x', 'y', 'lifeState', 'stateAge',
          'transitionAge', 'shootingAge', 'invincibility', 'shotAge', 'focused',
          'score', 'graze', 'pointValue', 'power', 'lives', 'lifePieces', 'bombs',
          'bombPieces', 'rank', 'visualSeed', 'visualCalls', 'gameplaySeed',
          'gameplayCalls', 'enemyCount', 'shots', 'character', 'subtype',
          'difficulty', 'stage', 'scaleFlags']
SHA = lambda data: hashlib.sha256(data).hexdigest()


def normalize(row):
    g, p = row['globals'], row['player']
    values = [row['stageFrame'], row['held'], row['pressed'], *p[:9],
              g[2], g[6], g[9], g[12], g[15], g[16], g[18], g[19], g[5],
              row['scriptRng'][0], row['scriptRng'][2], row['replayRng'][0],
              row['replayRng'][2], row['enemyCount'], row['shots'],
              *row['selection'], row['scaleFlags']]
    assert len(values) == 32
    return [x & 0xffffffff for x in values]


def main():
    assert not DOC.exists() and not OUT.exists(), 'New evidence only'
    OUT.mkdir(parents=True)
    bindings = {}

    def bind(path, expected=None, size=None):
        path = Path(path)
        if not path.is_absolute():
            path = ROOT / path
        path = path.resolve()
        key = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)
        if key not in bindings:
            h = hashlib.sha256()
            with path.open('rb') as f:
                while part := f.read(4 * 1024 * 1024):
                    h.update(part)
            bindings[key] = dict(bytes=path.stat().st_size, sha256=h.hexdigest())
        row = bindings[key]
        if expected is not None:
            assert row['sha256'] == expected, str(path)
        if size is not None:
            assert row['bytes'] == size, str(path)
        return dict(path=key, **row)

    def load(path, expected=None):
        bound = bind(path, expected)
        resolved = ROOT / bound['path']
        raw = resolved.read_bytes()
        assert SHA(raw) == bound['sha256']
        return json.loads(raw)

    def write(name, value):
        path = OUT / name
        path.write_bytes((json.dumps(value, separators=(',', ':')) + '\n').encode())
        return bind(path)

    def native_trace(path):
        native = load(path)
        path = ROOT / path
        receipt_path = path.with_suffix('.compact-receipt.json')
        if receipt_path.exists():
            receipt = load(receipt_path)
            assert receipt['allValuesEqual']
            bind(path, receipt['outputSha256'], receipt['outputBytes'])
            bind(receipt['source'], receipt['sourceSha256'], receipt['sourceBytes'])
            bind('tools/th14-native-trace-compact.py', receipt['toolSha256'])
            assert len(native['frames']) == receipt['frames']
        assert len(native['frames']) == native['capturedFrames']
        assert native['error'] == '' and not native['timedOut'] and native['noInputInjection']
        assert native['childGameStateOverrides'] == 1 and not native['ordinaryMenuLoaderVerified']
        init = native['caseInitialization']
        assert (init['address'], init['before'], init['after'], init['wordWrites'], init['replayManagerMode']) == ('0x4f58b8', 0x40, 0, 1, 1)
        assert init['beforeFirstPlayerInstruction'] and init['afterReadOnlyBootstrap']
        bind('tools/th14-native-stored-bootstrap-capture.py', native['warmReplayCaptureToolSha256'])
        bind('tools/th14-native-session-capture.py', native['captureToolSha256'])
        assert native['rngWrites'] == native['events'] == native['beamFallbacks'] == []
        return native

    engine_name = 'runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json'
    engine = load(engine_name)
    assert engine['title'] == 14 and engine['engineSources'] == len(engine['sources']) == 141
    assert len(engine['sourceHashes']) == 267
    bind('runtimes/th13/th13_web/artifacts/cpp/engine-th14.wasm', engine['sha256'], engine['bytes'])
    for name, digest in engine['sourceHashes'].items():
        bind(RT / name, digest)
    header_names = sorted(name for name in engine['sourceHashes'] if not name.endswith('.cpp'))
    headers_key = SHA('\n'.join(name + ' ' + engine['sourceHashes'][name] for name in header_names).encode())
    actual_objects = {}
    object_keys = {}
    for name in engine['sources']:
        path = ROOT / 'runtimes/th13/th13_web/artifacts/cpp/objects-th14' / (name.replace('/', '_') + '.o')
        key_path = Path(str(path) + '.key')
        key = SHA(json.dumps([engine['compileFlags'], headers_key, engine['sourceHashes'][name]], separators=(',', ':'), ensure_ascii=False).encode())
        assert key_path.read_text() == key
        actual_objects[name] = bind(path)['sha256']
        object_keys[name] = key
        bind(key_path)
    target = load('runtimes/th14/target.json')
    archive = bind(target['dataArchives']['th14.dat']['path'], size=target['dataArchives']['th14.dat']['bytes'])
    cases = []
    stored_reports = {}
    candidates = (
        ('reimua-lunatic-staged-loader-oct14', 'ReimuA Lunatic', 'th14_udzp01', [0, 0, 3], 'artifacts/th14/native-zps-reimua-lunatic-full-oct14/reference.compact.json'),
        ('reimub-lunatic-staged-loader-oct14', 'ReimuB Lunatic', 'th14_udzp02', [0, 1, 3], None),
        ('reimua-extra-staged-loader-oct14', 'ReimuA Extra', 'th14_udzp07', [0, 0, 4], 'artifacts/th14/native-zps-reimua-extra-full-oct14/reference.json'),
        ('sakuyaa-normal-staged-loader-oct14', 'SakuyaA Normal', 'th14_udzp05', [2, 0, 1], 'artifacts/th14/native-stored-warm-zps-continuous-long-oct13/reference-compact.json'),
    )
    for label, title, replay_name, selection, native_path in candidates:
        directory = HOME / label
        report = load(directory / 'report.json')
        stored_reports[label] = report
        assert report['productionPlaybackVerified'] and report['candidatePlaybackEnded'] and report['phase'] == 4
        assert not report['error'] and not report['gameOverRequested'] and not report['unsupported'] and not report['skipped']
        assert not report['forcedProgression'] and not report['invulnerabilityOverride'] and not report['gpuPrepared']
        assert report['allPhysicalCallbacksRetained'] and report['selectedCallbacks'] == report['frames']
        assert report['sourceHashes'] == engine['sourceHashes'] and report['objectHashes'] == actual_objects
        assert load(directory / 'engine-build.json', report['engineBuildSha256']) == engine
        assert report['archiveSha256'] == archive['sha256']
        bind('tools/th14-staged-loader-production-replay-check.mjs', report['toolSha256'])
        for name, digest in report['sourceHashes'].items():
            bind(directory / 'source' / name, digest)
        assert set(report['objectHashes']) == set(engine['sources'])
        for name, digest in report['objectHashes'].items():
            bind(directory / 'objects' / (name.replace('/', '_') + '.o'), digest)
        for name, digest in report['fixtureDependencyHashes'].items():
            bind(name, digest)
            bind(directory / 'fixture-source' / name, digest)
        for name, digest in report['fixtureHashes'].items():
            bind(RT / 'tests/cpp' / name, digest)
        bind(directory / 'production-clock-fixture.cpp', report['generatedFixtureSha256'])
        bind(directory / 'production-replay.wasm', report['wasmSha256'], report['wasmBytes'])
        replay = load('artifacts/th14/public-replay-reference/' + replay_name + '-source.json', report['replaySourceSha256'])
        bind('artifacts/th14/public-replay-reference/' + replay_name + '.rpy', report['replaySha256'], replay['bytes'])
        assert replay['sha256'] == report['replaySha256']
        assert [replay['character'], replay['subtype'], replay['difficulty']] == selection
        raw_path, active_path = directory / 'selected-state.u32', directory / 'callback-active.u8'
        bind(raw_path, report['selectedStateSha256'], report['selectedCallbacks'] * 128)
        bind(active_path, report['callbackActiveSha256'], report['selectedCallbacks'])
        raw, active = raw_path.read_bytes(), active_path.read_bytes()
        assert set(active) <= {0, 1} and active.count(0) == report['inactiveCallbacks']
        stage_counts, maxima = Counter(), {}
        for index, actual in enumerate(struct.iter_unpack('<32I', raw)):
            assert list(actual[27:30]) == selection
            stage_counts[actual[30]] += 1
            maxima[actual[30]] = max(maxima.get(actual[30], 0), actual[0])
        case = dict(title=title, label=label, physicalCallbacks=report['selectedCallbacks'], rawWords=report['selectedCallbacks'] * 32,
                    activeCallbacks=active.count(1), inactiveCallbacks=active.count(0), stages=dict(stage_counts), stageMaximumClocks=maxima,
                    productionReplayEnded=True, productionTerminalPhase=report['phase'], nativeRawComparisonAvailable=native_path is not None,
                    sourceFilesVerified=267, objectsVerified=141, replaySha256=report['replaySha256'], archiveSha256=archive['sha256'],
                    physicalInvocationOrder=True, allPhysicalRowsRetained=True, clockMode=report['clockMode'], captureRetirement=report['captureRetirement'])
        if native_path is not None:
            native = native_trace(native_path)
            count = len(native['frames'])
            assert count == report['selectedCallbacks']
            expected_words = array.array('I')
            differences = []
            counts, equal, difference_activity = Counter(), Counter(), Counter()
            for index, actual in enumerate(struct.iter_unpack('<32I', raw)):
                row = native['frames'][index]
                assert row['index'] == index and row['selection'][:3] == selection
                expected = normalize(row)
                expected_words.extend(expected)
                for field in range(32):
                    if actual[field] == expected[field]:
                        equal[FIELDS[field]] += 1
                    else:
                        item = dict(index=index, nativeStage=row['selection'][3], portableStage=actual[30],
                                    nativeStageFrame=row['stageFrame'], portableStageFrame=actual[0], active=active[index],
                                    field=FIELDS[field], portable=actual[field], native=expected[field])
                        differences.append(item)
                        counts[FIELDS[field]] += 1
                        difference_activity['active' if active[index] else 'inactive'] += 1
            if sys.byteorder != 'little':
                expected_words.byteswap()
            expected_path = OUT / (label + '-native-expected.u32')
            expected_path.write_bytes(expected_words.tobytes())
            gameplay = [row for row in differences if row['field'] not in ('visualSeed', 'visualCalls')]
            visual = sum(value for field, value in counts.items() if field in ('visualSeed', 'visualCalls'))
            full_diff = write(label + '-all-raw32-differences.json', differences)
            case.update(comparedNativeCallbacks=count, comparisonPassed=not differences, gameplayComparisonPassed=not gameplay,
                        allNativeCallbacksPaired=True, rawGameplayDifferences=len(gameplay), rawVisualDifferences=visual,
                        allFieldDifferenceCounts=dict(counts), equalWordCountsByField=dict(equal), allDifferenceActivityCounts=dict(difference_activity),
                        allGameplayDifferencesDuringInactiveCallbacks=all(not row['active'] for row in gameplay),
                        gameplayDifferenceRecords=gameplay, allDifferences=full_diff, nativeExpectedRaw32=bind(expected_path),
                        nativeCaseInitialization=native['caseInitialization'], nativeCaptureTimedOut=native['timedOut'],
                        nativeCapturedCallbacks=native['capturedFrames'], nativeRequestedCaptureBudget=native.get('requestedFrames', native.get('maxFrames')),
                        nativeOrdinaryTerminalVerified=False, nativeOrdinaryMenuLoaderVerified=False)
            del native, expected_words, differences, gameplay
            gc.collect()
        else:
            case['scope'] = 'Fresh physical ReimuB replay output and267/141 current custody verified; no matching full Native ReimuB oracle exists in this receipt. No Native equality count is inferred from another player or private v2.'
        cases.append(case)
        print(json.dumps(dict(case=title, callbacks=case['physicalCallbacks'], gameplay=case.get('rawGameplayDifferences'), visual=case.get('rawVisualDifferences')), ensure_ascii=False), flush=True)

    # Independently recompute the newly relinked full-object capture, including
    # every original detail failure array, instead of inheriting private counts.
    object_dir = ROOT / 'artifacts/th14/staged-loader-production-objects/reimua-lunatic-oct14'
    object_report = load(object_dir / 'report.json')
    assert object_report['productionObjectCaptureCompleted'] and object_report['productionVerified']
    assert not object_report['productionChanged'] and not object_report['gpuPrepared']
    assert object_report['comparedFrames'] == object_report['maximumCallbacks'] == 90793
    assert object_report['absentPlayerObservations'] == [] and object_report['physicalInvocationOrder'] and object_report['loadingCallbacksRetained']
    assert object_report['engineBuild'] == engine and object_report['objectHashes'] == actual_objects
    assert object_report['fixtureDependencyHashes'] == stored_reports[candidates[0][0]]['fixtureDependencyHashes']
    bind('tools/th14-staged-loader-production-objects-check.mjs', object_report['toolSha256'])
    bind('tools/th14-staged-loader-integration-objects-check.mjs', object_report['derivedCollectorSha256'])
    assert load(object_dir / 'engine-build.json', object_report['engineBuildSha256']) == engine
    bind(HOME / candidates[0][0] / 'report.json', object_report['productionPlaybackReportSha256'])
    bind(object_dir / 'production-playback-source-report.json', object_report['productionPlaybackReportSha256'])
    for name, digest in engine['sourceHashes'].items():
        bind(object_dir / 'source' / name, digest)
    for name, digest in actual_objects.items():
        path = object_dir / 'objects' / (name.replace('/', '_') + '.o')
        bind(path, digest)
        key_path = Path(str(path) + '.key')
        assert key_path.read_text() == object_keys[name]
        bind(key_path)
    for name, digest in object_report['fixtureDependencyHashes'].items():
        bind(object_dir / 'fixture-source' / name, digest)
    bind(object_dir / 'late-combat-fixture.cpp', object_report['fixtureSha256'])
    bind(object_dir / 'reference.wasm', object_report['wasmSha256'])
    bind(object_dir / 'portable-details.json', object_report['rawDetailSha256'])
    native = native_trace('artifacts/th14/native-zps-reimua-lunatic-full-oct14/reference.compact.json')
    assert object_report['nativeTraceSha256'] == bind(object_report['nativeTracePath'])['sha256']
    native_receipt = load('artifacts/th14/native-zps-reimua-lunatic-full-oct14/reference.compact.compact-receipt.json')
    assert object_report['compactReceipt'] == native_receipt
    details = load(object_dir / 'portable-details.json')
    portable_raw = (object_dir / 'portable-state.u32').read_bytes()
    bind(object_dir / 'portable-state.u32', object_report['portableStateSha256'])
    bind(object_dir / 'native-state.u32', object_report['nativeStateSha256'])
    assert portable_raw == (HOME / candidates[0][0] / 'selected-state.u32').read_bytes()
    assert len(details) == len(native['frames']) == len(portable_raw) // 128 == 90793
    mappings = [('popupWords', 'popupWords', False), ('popupCursor', 'popupCursor', False),
                ('enemies', 'enemyDetails', False), ('phases', 'enemyPhaseDetails', False),
                ('shots', 'liveShots', False), ('items', 'itemDetails', True), ('bullets', 'bulletDetails', True),
                ('damageAreas', 'damageAreas', False), ('enemyHitboxAngles', 'enemyHitboxAngles', False),
                ('enemyIds', 'enemyIds', False), ('shotRewards', 'shotRewardCounters', False), ('enemyNextId', 'enemyNextId', False)]
    serialized = lambda values: sorted(json.dumps(row, separators=(',', ':')) for row in values)
    gameplay, visual, detail_differences = [], [], []
    expected_words = array.array('I')
    captured, matched, windows, active_windows = Counter(), Counter(), Counter(), Counter()
    for index, actual in enumerate(struct.iter_unpack('<32I', portable_raw)):
        row, portable = native['frames'][index], details[index]
        assert row['index'] == portable['index'] == index and portable['stage'] == actual[30] and portable['stageFrame'] == actual[0]
        expected = normalize(row)
        expected_words.extend(expected)
        for field in range(32):
            if actual[field] != expected[field]:
                target_differences = visual if field in (21, 22) else gameplay
                target_differences.append(dict(index=index, stage=actual[30], frame=actual[0], field=object_report['fieldNames'][field], port=actual[field], native=expected[field]))
        if 15820 <= row['stageFrame'] <= 15890:
            windows[row['selection'][3]] += 1
            if portable['active']:
                active_windows[row['selection'][3]] += 1
        for key, native_key, unordered in mappings:
            if native_key not in row:
                continue
            captured[key] += 1
            a, b = portable[key], row[native_key]
            equal = serialized(a) == serialized(b) if unordered else a == b
            if equal:
                matched[key] += 1
            else:
                detail_differences.append(dict(index=index, stage=actual[30], frame=actual[0], kind=key, port=a, native=b))
    if sys.byteorder != 'little':
        expected_words.byteswap()
    assert expected_words.tobytes() == (object_dir / 'native-state.u32').read_bytes()
    assert gameplay == object_report['differences'] and visual == object_report['startupVisualDifferences']
    assert detail_differences == object_report['detailDifferences']
    assert object_report['passed'] == (not gameplay and not detail_differences)
    inactive = [row for row in detail_differences if not details[row['index']]['active']]
    active = [row for row in detail_differences if details[row['index']]['active']]
    changed_areas, columns = [], Counter()
    for row in active:
        if row['kind'] != 'damageAreas':
            continue
        a = {value[0]: value for value in row['port']}
        b = {value[0]: value for value in row['native']}
        assert len(a) == len(row['port']) and len(b) == len(row['native'])
        for slot in sorted(a.keys() & b.keys()):
            assert len(a[slot]) == len(b[slot]) == 20
            changed = [i for i in range(20) if a[slot][i] != b[slot][i]]
            if changed:
                columns.update(changed)
                changed_areas.append(dict(index=row['index'], stage=row['stage'], frame=row['frame'], slot=slot, changedColumns=changed,
                                          portableWords=a[slot], nativeWords=b[slot]))
    object_evidence = dict(currentProductionObjectEvidenceVerified=True, comparisonPassed=object_report['passed'],
                           comparedCallbacks=len(details), allNativeCallbacksPaired=True, rawWords=len(details) * 32,
                           productionRaw32IdenticalToSeparatePhysicalReplay=True, capturedDetailFields=dict(captured), equalDetailFields=dict(matched),
                           rawGameplayDifferences=len(gameplay), rawVisualDifferences=len(visual), retainedDetailDifferences=len(detail_differences),
                           inactiveLoadingDetailDifferences=len(inactive), activeBattleDetailDifferences=len(active),
                           inactiveLoadingDetailDifferenceKinds=dict(Counter(row['kind'] for row in inactive)),
                           activeBattleDetailDifferenceKinds=dict(Counter(row['kind'] for row in active)),
                           allInactiveDetailDifferencesAreFrameZeroEnemyNextId=all(row['kind'] == 'enemyNextId' and row['frame'] == 0 for row in inactive),
                           allRawGameplayDifferencesDuringInactiveCallbacks=all(not details[row['index']]['active'] for row in gameplay),
                           lateWindow=[15820, 15890], pairedLateWindowCallbacks=dict(windows), activeLateWindowCallbacks=dict(active_windows),
                           rawGameplayDifferenceRecords=gameplay, detailDifferenceRecords=detail_differences,
                           activeAreaDifferenceColumns=sorted(columns), activeAreaDifferenceColumnCounts=dict(columns), activeAreaChangedRows=changed_areas,
                           nativeCapturedCallbacks=native['capturedFrames'], nativeOrdinaryTerminalVerified=False, productionTerminalPhase=object_report['terminalPhase'],
                           wasmSha256=object_report['wasmSha256'], sourceFilesVerified=267, objectsVerified=141,
                           scope='Fresh current-production141-object link and physical run; every90793 raw32 and captured detail independently recomputed. Stable area-slot joins describe changed columns only after retaining the complete original arrays; uninitialized Native Z is observable and stays failed. Requested Native budget is not a Native ordinary terminal. Headless preparation/declared clock/no-target retirement do not certify SDL uploads, scheduling, pixels, audio, ordinary startup or whole-game equality.')
    result = dict(productionRawEvidenceVerified=True, completeGame=False, nativeEquivalent=False, sourceFilesVerified=267, sourceHashes=engine['sourceHashes'],
                  engineObjectsVerified=141, objectHashes=actual_objects, objectKeys=object_keys, cases=cases, productionObjects=object_evidence,
                  allFields=FIELDS, bindings=bindings, bindingCount=len(bindings), toolSha256=SHA(Path(__file__).read_bytes()),
                  scope='Fresh ROOT production evidence, never a private v2/v3 module pass. All current267 source and141 exact object/key hashes, each archived source/object/fixture dependency, intact public inputs, original DAT, generated clock fixture and module are bound. Three actual Native raw32 baselines are compared in physical order without trimming/resynchronization/masking; every difference is preserved in newly bound private arrays. ReimuB has fresh full physical output but no matching Native oracle here. Native compaction custody includes exact original source and all-values-equal receipt, without separately reparsing the historical whitespace source. Current production ends do not prove the Native requested90793 capture budget reached an ordinary end, full-game1:1, ordinary loader timing, all modes, owner-memory equivalence, graphics/audio or browser storage.')
    DOC.write_bytes((json.dumps(result, indent=2) + '\n').encode())
    print(json.dumps(dict(report=bind(DOC), cases=[dict(title=x['title'], gameplay=x.get('rawGameplayDifferences'), visual=x.get('rawVisualDifferences')) for x in cases], objects={k:object_evidence[k] for k in ['comparedCallbacks', 'rawGameplayDifferences', 'retainedDetailDifferences', 'inactiveLoadingDetailDifferences', 'activeBattleDetailDifferences']}, bindingCount=result['bindingCount'])), flush=True)


if __name__ == '__main__':
    main()
