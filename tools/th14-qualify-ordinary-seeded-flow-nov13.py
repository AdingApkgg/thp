"""Qualify an input-only ordinary clear with a declared startup clock.

This is a controlled-startup case, not coverage of arbitrary startup seeds.
No cross-engine per-frame equality or whole-game completion is asserted.
"""
from pathlib import Path
from collections import Counter
import ast
import hashlib
import importlib.util
import json
import struct

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/ordinary-keyscript-nov13'
O = H / 'seeded-full-flow-proof'
load = lambda p: json.loads(p.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    O.mkdir(exist_ok=False)
    build = load(H / 'component/build.json')
    for name, digest in {**build['sourceBindingsByMode']['candidate'], **build['objectBindings']}.items():
        assert sha(R / name) == digest, name
    reports = {}
    for name in ['seeded-flow-v1', 'read-seeded-v1']:
        directory = H / name
        report = load(directory / 'report.json')
        assert report['passed'] and report['retired'] and report['closed']
        assert report['exception'] is None and not report['errors']
        assert report['driverSha256'] == sha(directory / 'executed-driver.mjs')
        assert report['sourceWasmSha256'] == sha(H / 'component/candidate.wasm')
        assert not report['completionBoundaryInvokedDirectly']
        assert all(w['closed'] and w['exitCode'] == 0 for w in report['physicalWorkers'])
        platform = load(directory / 'platform.json')
        assert not platform['audibleOutput'] and not platform['pendingTimers']
        assert not any(platform['liveObjects'].values())
        clock = load(directory / 'process-clock.json')
        assert not clock['active'] and clock['beginCalls'] == clock['endCalls'] == 1
        reports[name] = report
    run = reports['seeded-flow-v1']
    assert run['outcome'] == 'natural-clear-results-saved' and run['endingSeen'] and run['resultSeen']
    assert run['startupClockSelectedForDeterministicInputCoverage'] and run['noRngStateWrites']
    assert (run['originalClock'], run['selectedClock']) == (241183420, 241224550)
    assert not run['recordedGameStateRestored'] and not run['referenceRowsFedBack']
    assert run['inputProviderIsHeldKeysOnly'] and sorted(run['visitedStages']) == list(range(1, 7))
    writer = H / 'seeded-flow-v1'
    initial = load(writer / 'ordinary-initial-player.json')['flow']
    ending = load(writer / 'natural-ending-entered.json')['flow']
    result = load(writer / 'natural-result-and-flush.json')
    fresh = load(H / 'read-seeded-v1/fresh-title-read.json')['flow']
    assert initial[7:11] == [0, 0, 0, 0] and initial[12:18] == [0] * 6
    assert ending[0] == 5 and ending[3] == 2
    assert result['flow'][5] == 14 and fresh[5] == 1
    for flow in [ending, result['flow'], fresh]:
        assert flow[7:11] == [1, 1, 1, 17]
    for flow in [result['flow'], fresh]:
        assert flow[11:18] == [1, 0, 1, 0, 0, 0, 0]
    stages = Counter()
    raw = (writer / 'observations.u32').read_bytes()
    first, last = None, None
    for number, row in enumerate(struct.iter_unpack('<114I', raw), 1):
        assert row[0] == number and row[28:31] == (0, 1, 1)
        assert 1 <= row[31] <= 6
        stages[row[31]] += 1
        if first is None:
            first = row
        last = row
    assert sum(stages.values()) == 122385 and set(stages) == set(range(1, 7))
    assert first[24] == 4607
    # The startup seed is selected through the normal clock input, not written
    # into the active game's RNG. Record the prediction separately from play.
    seed = 52070
    for _ in range(494):
        mixed = ((seed ^ 0x9630) - 0x6553) & 65535
        seed = ((mixed << 2) | (mixed >> 14)) & 65535
    assert seed == 4607
    codec_source = R / 'tools/th14-audit-root-full-extra-nov08.py'
    function = next(n for n in ast.parse(codec_source.read_text()).body
                    if isinstance(n, ast.FunctionDef) and n.name == 'decode_score')
    spec = importlib.util.spec_from_file_location('seeded_score_codec', R / 'tools/th-replay-container.py')
    mirror = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mirror)
    scope = dict(struct=struct, mirror=mirror)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[])), str(codec_source), 'exec'), scope)
    encoded = (writer / 'save/scoreth14.dat').read_bytes()
    assert (H / 'read-seeded-v1/save/scoreth14.dat').read_bytes() == encoded
    decoded = scope['decode_score'](encoded)
    assert len(decoded) == 149076
    for i in range(8):
        start, size = i * 0x5298, 0x5298 if i < 7 else 0x42c
        record = decoded[start:start + size]
        assert struct.unpack_from('<I', record)[0] == (0x15243 if i < 7 else 0x15453)
        assert struct.unpack_from('<I', record, 8)[0] == size
        assert sum(record[8:]) == struct.unpack_from('<I', record, 4)[0]
        if i < 7:
            assert struct.unpack_from('<I', record, 12)[0] == i
    assert struct.unpack_from('<I', decoded, 0x5298 + 0x7c4)[0] == 1
    assert struct.unpack_from('<I', decoded, 0x5298 + 0x7e0)[0] == 1
    rank = 0x5298 + 0x10 + 0x118
    assert struct.unpack_from('<I', decoded, rank)[0] == result['rank']['scoreUnits'] == 91452576
    assert list(decoded[rank + 4:rank + 6]) == [8, 0]
    assert [decoded[7 * 0x5298 + n] for n in [0x16, 0x18]] == [1, 17]
    (O / 'observed-decoded.bin').write_bytes(decoded)
    report = dict(passed=True, acceptanceStandard='observable-behavior-alignment',
                  startupClockSelectedForDeterministicInputCoverage=True,
                  originalClock=241183420, selectedClock=241224550,
                  directGameStateOrCompletionWrites=False, replayStateRestoredIntoOrdinaryGame=False,
                  actualOrdinaryClearWithDeclaredStartupClock=True, arbitraryStartupSeedsCovered=False,
                  callbacks=sum(stages.values()), stageCallbacks=dict(stages),
                  actualEndingStaffAndResults=True, freshApplicationUnlockRead=True,
                  clearCount=1, noContinueClearCount=1, extraAvailableLoadouts=['Reimu B'],
                  finalScoreUnits=result['rank']['scoreUnits'], finalDisplayedScore=result['rank']['scoreUnits'] * 10,
                  lastObservedPrePlayerScoreUnits=last[13], scoreEncodedBytes=len(encoded),
                  scoreDecodedBytes=len(decoded), scoreSha256=hashlib.sha256(encoded).hexdigest(),
                  decodedSha256=hashlib.sha256(decoded).hexdigest(), recordChecksumsVerified=8,
                  reportHashes={n: sha(H / n / 'report.json') for n in reports},
                  elapsedSeconds=run['elapsedSeconds'], allMeasuredResourcesRetired=True, silent=True,
                  graphicsRecordingOnly=True, originalWholeGameNaturalClearCompared=False,
                  allModesAccepted=False, completeGame=False)
    (O / 'qualified.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
