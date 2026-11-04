"""Recompute the sealed Hard run and qualify finite inferred REP read splits.

Public output contains counters, addresses, paths and hashes, never raw game
assets or observations. Equality does not accept independent thread timing.
"""
from pathlib import Path
import argparse, hashlib, json, struct

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/reimub-hard-full-context-nov05'
F = H / 'retry1/full'
N = F / 'native'
M = F / 'current-core-comparison-v4/model'
SHA = lambda raw: hashlib.sha256(raw).hexdigest()

def verify():
    bindings = {}
    def raw(path):
        value = path.read_bytes()
        bindings[path.relative_to(R).as_posix()] = dict(bytes=len(value), sha256=SHA(value))
        return value
    def load(path): return json.loads(raw(path))
    native = load(N / 'report.json'); seal = load(F / 'native-sealed.json')
    model = load(M / 'report.json'); gate = load(F / 'raw-verified-v4.json')
    count = native['callbacks']; assert count == 107243
    assert native['recordedStages'] == [1, 2, 3, 4, 5, 6]
    assert seal['originalCaptureGatePassed'] and all(seal['checks'].values())
    assert seal['nativeReportSha256'] == SHA(raw(N / 'report.json'))
    assert seal['processEndSha256'] == SHA(raw(F / 'process-end.json'))
    assert not native['debugErrors'] and not native['error'] and native['childExited']
    assert native['configuredMusicAndSoundVolumeZero'] and native['rngOrCounterWrites'] == 0
    assert native['gameStateWordWrites'] == 1 and native['observedForcedReplayEndMenu']
    assert native['sourceSha256'] == SHA(raw(N / 'observer-source.py')) == SHA(raw(H / 'observer.py'))
    assert load(F / 'current-core-comparison-v4/process-end.json')['exitCode'] == 0
    driver = R / 'tools/th14-compare-native-hard-rep-split-v4-nov05.mjs'
    assert SHA(raw(driver)) == model['comparisonToolSha256'] == '1af7e21434fa1245980cbe7d020d238344dba213d4e99afef9b111280d104a61'
    selected = raw(N / 'selected-state.u32')
    assert len(selected) == count * 128 and selected == raw(M / 'selected-state.u32') == raw(M / 'native-selected-state.u32')
    assert model['allRaw32ByteIdentical'] and not model['differenceCounts'] and model['callbacks'] == count
    camera = raw(N / 'world-camera.raw'); tail = raw(N / 'world-camera-tail.u32')
    actual = raw(M / 'full-camera.u32')
    assert len(camera) == count * 292 and len(tail) == count * 8 and len(actual) == (count - 1) * 300
    for index in range(1, count):
        assert actual[(index-1)*300:index*300] == camera[index*292:(index+1)*292] + tail[index*8:(index+1)*8]
    cursor = raw(N / 'replay-cursor.u32'); actual = raw(M / 'replay-cursor.u32')
    assert len(cursor) == count * 56 and len(actual) == (count-1) * 16
    for index in range(1, count):
        assert struct.unpack_from('<4I', actual, (index-1)*16) == tuple(struct.unpack_from('<I', cursor, index*56 + i*4)[0] for i in [3, 7, 8, 9])
    assert raw(N / 'hud-score.u32') == raw(M / 'portable-hud.u32')
    assert gate['verifiedFiniteEvidence'] and gate['callbacks'] == count
    assert (gate['vm303Rows'], gate['combatCheckpoints'], gate['nonemptyCombatCheckpoints'], gate['orderedPublications']) == (1240, 1081, 312, 5189)
    assert gate['verifierSha256'] == SHA(raw(R / 'tools/th14-verify-native-campaign.py'))
    for name, item in gate['bindings'].items():
        value = raw(R / name); assert len(value) == item['bytes'] and SHA(value) == item['sha256']
    split = load(M / 'perspective-rep-split-report.json')
    assert split['nativeReadGenerationClassificationUsed'] and split['noNativeStateValuesProvidedToEngine']
    assert not split['independentTimingAccepted'] and not split['exactOriginalScheduleRecovered']
    assert [(x['stage'], x['callback'], x['pause'], x['start'], x['end']) for x in split['windows']] == [(3, 22840, 13, 4, 5), (5, 56970, 16, 0, 2)]
    reads = [json.loads(line) for line in raw(N / 'worker-camera-source-read-events.jsonl').splitlines()]
    copies = [json.loads(line) for line in raw(N / 'scene-camera-copy-events.jsonl').splitlines()]
    for snapshot in split['snapshots']:
        w = snapshot['window']; state = snapshot['state']; stage = w['stage']
        assert not snapshot['differences'] and snapshot['prefixEqual']
        assert state[7:9] == [1, 1] and min(state[9:11]) > 0 and state[11:] == [1, 1, 0]
        expected = bytes.fromhex(next(x['copiedCameraHex'] for x in copies if x['stage'] == stage and x['event'] == 'scene-camera-copy-after'))
        prefix = bytes.fromhex(next(x['copiedCameraHex'] for x in reads if x['stage'] == stage))[:w['pause']*4]
        assert raw(M / f'perspective-rep-scene-stage{stage}.u32') == expected
        assert snapshot['actualSha256'] == snapshot['nativeSha256'] == SHA(expected)
        assert snapshot['prefixSha256'] == snapshot['nativePrefixSha256'] == SHA(prefix)
    strict = load(F / 'strict-gates-v4.json')
    assert [(x['gate'], x['passed']) for x in strict['results']] == [('exceptions', True), ('initialize', True), ('scene', False)]
    assert not strict['overallStrictAccepted'] and not strict['strictSceneWhitelistModified']
    for item in strict['results']:
        assert SHA(raw(F / ('strict-' + item['gate'] + '-v4.log'))) == item['logSha256']
    build = load(H / 'retry1/perspective-rep-build/observer-build.json')
    assert build['engineObjectsReusedForThisLink'] == 141 and build['engineSourcesRecompiledForThisLink'] == 0
    assert build['wasmSha256'] == model['wasmSha256']
    control = F / 'read-through-control-nov05'
    control_end = load(control / 'process-end.json'); control_plan = load(control / 'plan.json')
    assert control_end['expectedFailureRetained'] and control_end['exitCode'] != 0
    assert control_plan['parentDriverSha256'] == model['comparisonToolSha256']
    assert control_plan['disabledOnlyInferredPerspectiveRepReadWaits']
    negative_camera = load(control / 'model/full-camera-report.json')
    assert not negative_camera['allExpandedCapturedWordsEqual'] and negative_camera['counts']
    assert SHA(raw(R / 'tools/th14-hard-rep-read-through-control-generated-nov05.mjs')) == control_plan['controlDriverSha256']
    failures = []
    for directory in ['current-core-comparison', 'current-core-comparison-v2']:
        end = load(F / directory / 'process-end.json'); assert end['exitCode'] != 0
        failures.append(dict(path=(F / directory).relative_to(R).as_posix(), exitCode=end['exitCode'], logSha256=SHA(raw(F / directory / 'process.log'))))
    timeout = load(H / 'full/native/report.json'); assert timeout['callbacks'] == 0 and timeout['error']
    raw(H / 'full/process-end.json')
    for name in ['th14-build-perspective-rep-split-nov05.py', 'th14-prepare-hard-rep-split-v4-nov05.py', 'th14-hard-rep-split-read-through-control-nov05.py']:
        raw(R / 'tools' / name)
    raw(R / 'runtimes/th12/th12_web/tests/cpp/th14-perspective-rep-split-fixture-nov05.cpp')
    return dict(schema='th14/hard-full-context/1', verifiedFiniteInferredReadEvidence=True, selection=[0,1,2,1], callbacks=count,
        nativeDebugExceptions=0, nativeEndMenuObserved=True, allSelected32Equal=True, all75CameraWordsEqual=True,
        comparedCameraWords=(count-1)*75, firstComparedCameraCallback=2, replayCursorFields=4, firstComparedCursorCallback=2,
        allHud2Equal=True, vm303Rows=1240, combatCheckpoints=1081, nonemptyCombatCheckpoints=312, initialPublications=5189,
        perspectiveRepSplits=split['windows'], readThroughNegativeCameraCounts=negative_camera['counts'],
        nativeReadGenerationClassificationUsed=True, nativeStateValuesProvidedToEngine=False,
        exactOriginalScheduleRecovered=False, ordinaryIndependentThreadTimingAcceptance=False,
        strictInitializeAccepted=True, strictSceneAccepted=False, strictWhitelistModified=False,
        preparationFailuresRetained=failures, priorStartupTimeoutCauseExplained=False,
        modelWasmSha256=model['wasmSha256'], modelDriverSha256=model['comparisonToolSha256'],
        productionGameplaySourcesChanged=False, browserAcceptance=False, wholeOriginalFramebufferOrPcmAccepted=False,
        limits=['Native read prefixes classify the inferred split schedule. No camera/RNG/VM values are supplied to the engine.',
                'Finite field equality under declared original clocks does not accept exact instruction placement or independent scheduling.',
                'VM and combat samples, initial publications and selected fields do not accept complete objects, all modes, full GPU/PCM or persistence.',
                'The zero-Player startup timeout and comparator preparation failures remain retained; no exception gate is waived.'],
        completeGame=False, nativeEquivalent=False, verifierSha256=SHA(Path(__file__).read_bytes()), bindings=bindings)

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--output', type=Path, required=True); p.add_argument('--check', action='store_true')
    a = p.parse_args(); out = a.output.resolve()
    assert out.is_relative_to(R / 'artifacts/th14') or out.is_relative_to(R / 'docs/porting')
    result = verify()
    if a.check: assert json.loads(out.read_bytes()) == result
    else:
        assert not out.exists(); out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({key: result[key] for key in ['verifiedFiniteInferredReadEvidence','callbacks','comparedCameraWords','vm303Rows','combatCheckpoints','strictInitializeAccepted','strictSceneAccepted']}))
