"""Recheck native construction blocks, compiled restore and real Application.

Produces source/hash metadata only. The original decoded input, instruction
write records, images and saved files stay private. This is finite evidence,
not ordinary-original GUI or whole-game equivalence acceptance.
"""
from pathlib import Path
import argparse
import hashlib
import importlib
import json
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda raw: hashlib.sha256(raw).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--home', type=Path, default=ROOT / 'artifacts/th14/replay-construction-oct30')
    p.add_argument('--output', type=Path, default=ROOT / 'docs/porting/th14-replay-construction-oct30.json')
    p.add_argument('--check', action='store_true')
    args = p.parse_args()
    home = args.home.resolve()
    bindings = {}

    def read(path):
        raw = path.read_bytes()
        bindings[path.relative_to(ROOT).as_posix()] = dict(bytes=len(raw), sha256=SHA(raw))
        return raw

    def load(path):
        return json.loads(read(path))

    native = load(home / 'native-v3/native.json')
    assert native['completed'] and native['initialCases'] == native['existingStageCases'] == 288
    assert native['declaredDecodedVirtualInputsOnly'] and not native['originalInstructionsModified']
    assert not native['ordinaryMenuInitializationAccepted'] and not native['nativeFileLoadExecuted']
    assert native['toolSha256'] == SHA(read(ROOT / 'tools/th14-replay-construction-native-oct30.py')) == SHA(read(home / 'native-v3/run-tool.py'))
    sys.path[:0] = [str(ROOT / 'tools/tmp/th14-analysis-python'), str(ROOT / 'tools')]
    image = importlib.import_module('th-anm-handlers').handlers(14)[0]
    assert SHA(image.data) == native['executableSha256'] == 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    for row in native['instructionSlices']:
        assert SHA(image.read(row['address'], row['bytes'])) == row['sha256']
    decoded = read(ROOT / 'artifacts/th14/replay-coverage-input-oct26/marisab-normal-kmk/th14_ud0593-decoded.bin')
    assert SHA(decoded) == native['decodedSha256']
    headers = {}
    offset = 0x94
    for _ in range(struct.unpack_from('<I', decoded, 0x78)[0]):
        header = decoded[offset:offset + 0xdc]
        headers[struct.unpack_from('<H', header)[0]] = header
        offset += 0xdc + struct.unpack_from('<I', header, 8)[0]
    assert offset == len(decoded) and sorted(headers) == list(range(1, 7))
    before = load(home / 'model-before/comparison.json')
    after = load(home / 'model-after/comparison.json')
    assert before['initialExactCases'] == 0 and after['initialExactCases'] == 288
    assert before['existingStageExactCases'] == after['existingStageExactCases'] == 288
    assert before['legacyInitialCallContract'] and not after['legacyInitialCallContract']
    selected = [2, 3, 5, 6, 8, 9, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]
    assert len(before['rows']) == len(after['rows']) == len(native['cases']) == 576
    for old, new, case in zip(before['rows'], after['rows'], native['cases']):
        header = headers[case['stage']]
        seed = struct.unpack_from('<H', header, 2)[0]
        expected_rng = [(case['initialScriptSeed'] if case['initial'] else seed) | 0xa5a50000,
                        case['initialCalls'], seed | 0x5a5a0000, 0]
        assert case['rngWords'] == expected_rng
        expected = expected_rng + [struct.unpack_from('<28I', header, 0x14)[i] for i in selected]
        assert old['expected'] == new['expected'] == new['actual'] == expected and new['equal']
        assert old['differingWords'] == ([0] if case['initial'] else [])
        if case['initial']:
            rng_writes = [w for w in case['writeSequence'] if 0x4db508 <= w['address'] < 0x4db518]
            assert [(w['pc'], w['address'], w['bytes'], w['value']) for w in rng_writes] == [
                (0x454a41, 0x4db510, 2, seed), (0x454a47, 0x4db514, 4, 0)]
    for folder, comparison in [('model-before', before), ('model-after', after)]:
        assert comparison['nativeReportSha256'] == SHA(read(home / 'native-v3/native.json'))
        assert comparison['wasmSha256'] == SHA(read(home / folder / 'probe.wasm'))
        assert comparison['actualRestoreBodyCompiled'] and not comparison['wholeGameSessionCompiled']
        assert comparison['toolSha256'] == SHA(read(home / folder / 'run-tool.py')) == SHA(read(ROOT / 'tools/th14-replay-construction-compare-oct30.py'))
    for name, row in after['sourceBindings'].items():
        assert SHA(read(ROOT / name)) == row['sha256']
    session_name = 'runtimes/th12/th12_web/cpp/game/GameSession.cpp'
    courier = ROOT / 'tools/tmp/github-source-release'
    old_session = subprocess.check_output(['git', '-C', str(courier), 'show', '59ac9c67b850ed0348fdc6d047b1cd80aa02ae79:' + session_name])
    assert SHA(old_session) == before['sourceBindings'][session_name]['sha256']
    branches = native['branches']
    assert len(branches) == 8 and native['supervisorMode13CallsControlMode1']
    for row in branches:
        assert row['target'] == (0x456050 if row['flags'] & 2 else 0x454e60)
        assert row['stableFlags'] == row['flags'] & ~0xb
    core = load(home / 'core-build/observer-build.json')
    assert core['engineSourcesRecompiledForThisLink'] == 2 and core['engineObjectsReusedForThisLink'] == 139
    assert core['unrelatedRootResourceCryptExcluded'] and len(core['objectBindings']) == 141
    for row in core['objectBindings']:
        assert SHA(read(Path(row['path']))) == row['sha256']
    for name, digest in core['sourceHashes'].items():
        if name.endswith('/ResourceCrypt.cpp'):
            assert digest == 'd57118f1114f3909c42a2e99e7df30e625f6563247a8118cd14bb9f68a0f97ef'
            assert SHA((ROOT / 'runtimes/th12' / name).read_bytes()) == 'a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45'
        else:
            assert SHA(read(ROOT / 'runtimes/th12' / name)) == digest
    for name, digest in core['headerHashes'].items():
        assert SHA(read(ROOT / 'runtimes/th12' / name)) == digest
    builds = {}
    runs = {}
    for label in ('legacy', 'observed'):
        build = load(home / ('application-' + label) / 'build.json')
        run = load(home / ('run-' + label) / 'report.json')
        assert build['wasmSha256'] == SHA(read(home / ('application-' + label) / 'application.wasm')) == run['wasmSha256']
        assert run['toolSha256'] == SHA(read(home / ('run-' + label) / 'run-tool.py')) == SHA(read(ROOT / 'tools/th14-native-application-process-host-oct27.py'))
        assert run['completed'] and not run['error'] and run['frames'] == 782 and len(run['checks']) == 21
        assert all(c['passed'] and c['actual'] == c['expected'] for c in run['checks'])
        assert run['physicalAudioDevicesOpened'] == 0 and not run['browserAcceptance']
        assert run['replayConstructionObservationOnly'] and len(run['replayConstructionTransitions']) == 1
        for name, row in build['sourceBindings'].items():
            assert SHA(read(ROOT / name)) == row['sha256']
        for row in build['coreObjects']:
            assert SHA(read(Path(row['path']))) == row['sha256']
        for name, digest in build['newObjects'].items():
            assert SHA(read(home / ('application-' + label) / name)) == digest
        for capture in run['captures']:
            assert SHA(read(home / ('run-' + label) / capture['file'])) == capture['sha256']
            live = capture['liveAnimations']
            assert SHA(read(home / ('run-' + label) / live['file'])) == live['sha256']
        assert run['scenarioSha256'] == SHA(read(home / 'scenario.json'))
        replay = run['initialSave']['replay/th14_01.rpy']
        assert replay == run['finalSave']['replay/th14_01.rpy']
        assert replay['sha256'] == SHA(read(home / ('run-' + label) / 'save/replay/th14_01.rpy')) == '28d9d29a34cf1dd0e67d67a82c1f0a5f7c508543271e0f1b1e4cbed527ff7353'
        builds[label] = build
        runs[label] = run
    assert builds['observed']['coreBuildSha256'] == SHA(read(home / 'core-build/observer-build.json'))
    assert builds['observed']['coreSourceHashes'] == core['sourceHashes']
    assert {n for n in core['sourceHashes'] if core['sourceHashes'][n] != builds['legacy']['coreSourceHashes'][n]} == {
        'th12_web/cpp/game/GameSession.cpp', 'th12_web/cpp/game/Replay.cpp'}
    old_transition = runs['legacy']['replayConstructionTransitions'][0]
    new_transition = runs['observed']['replayConstructionTransitions'][0]
    assert old_transition['before'] == new_transition['before']
    assert old_transition['frame'] == new_transition['frame'] == 560
    assert old_transition['boundary'] == new_transition['boundary'] == 'tick'
    old_state, new_state = old_transition['after'], new_transition['after']
    pre = new_transition['before']
    calls = (new_state[5] - pre[5]) & 0xffffffff
    assert calls == 20 and old_state[5] == new_state[5]

    def advance(seed, count):
        for _ in range(count):
            mixed = ((seed ^ 0x9630) - 0x6553) & 0xffff
            seed = ((mixed << 2) | (mixed >> 14)) & 0xffff
        return seed

    seed = struct.unpack_from('<H', headers[1], 2)[0]
    assert new_state[4] == advance(pre[4], calls) != old_state[4]
    assert old_state[4] == advance(seed, calls)
    assert new_state[3] == 0 and old_state[3] == 2
    assert old_state[6:] == new_state[6:] == [seed, 0, 1, 0]
    assert [a['state'] for a in runs['legacy']['actions']] == [a['state'] for a in runs['observed']['actions']]
    assert runs['legacy']['pcmFrames'] == runs['observed']['pcmFrames'] == 417792
    assert runs['legacy']['pcmSha256'] == runs['observed']['pcmSha256']
    full_raw = read(home / 'ordinary-full/report.json')
    full = json.loads(full_raw)
    failure = load(ROOT / 'docs/porting/th14-replay-construction-full-failure-oct30.json')
    plan = load(home / 'full-plan.json')
    assert not full['completed'] and full['error'] == "AssertionError('Declared state was not reached within the frame budget')"
    assert full['frames'] == failure['frames'] == 27251 and len(full['checks']) == failure['assertionsPassed'] == 20
    assert failure['reportSha256'] == SHA(full_raw) and failure['planSha256'] == SHA(read(home / 'full-plan.json'))
    assert full['wasmSha256'] == builds['observed']['wasmSha256'] == failure['wasmSha256']
    assert full['toolSha256'] == SHA(read(home / 'ordinary-full/run-tool.py')) == SHA(read(ROOT / 'tools/th14-native-application-process-host-oct27.py'))
    assert full['scenarioSha256'] == plan['scenarioSha256'] == SHA(read(ROOT / plan['scenario']))
    assert plan['maximumFrames'] == 150000 and plan['maximumWallSeconds'] == 3600
    assert plan['minimumFreeBytes'] == 100 * 1024**3 and plan['maximumOutputBytes'] == 128 * 1024**2
    assert plan['scenarioUpperBoundFrames'] == 129854
    assert failure['observedStages'] == sorted({r['state'][1] for r in full['rows'] if r['state'][1]}) == [1, 2]
    last = full['rows'][-1]['state']
    assert last[0:2] == [2, 2] and last[7] == failure['finalLivingStock'] == 0xffffffff
    assert last[9] == failure['finalScoreUnits'] == 3285179
    assert full['physicalAudioDevicesOpened'] == 0 and not failure['fullReplayAccepted']
    assert full['initialSave']['replay/th14_01.rpy'] == full['finalSave']['replay/th14_01.rpy']
    assert not (home / 'full-accepted.json').exists()
    for capture in full['captures']:
        assert SHA(read(home / 'ordinary-full' / capture['file'])) == capture['sha256']
        live = capture['liveAnimations']
        assert SHA(read(home / 'ordinary-full' / live['file'])) == live['sha256']
    result = dict(schema='th14/replay-construction-evidence/1', verifiedFiniteConstructionRepair=True,
                  originalInitialCases=288, originalExistingStageCases=288,
                  oldInitialExactCases=0, correctedInitialExactCases=288, existingStageExactCases=288,
                  nativeInitialScriptSeedPreserved=True, existingStageBothSeedsRestored=True,
                  stableTransientReplayFlagCleared=True, actualRestoreBodyCompiled=True,
                  actualApplicationCoreObjects=141, coreSourcesRecompiled=2, coreObjectsReused=139,
                  actualApplicationFramesPerVersion=782, actualApplicationAssertionsPerVersion=21,
                  samePreActivationState=True, actualScriptRngContinuesWithoutSeedReplacement=True,
                  activationScriptCallsObserved=20, inputReplayUnchanged=True, physicalAudioDevicesOpened=0,
                  initialPcmFramesPerVersion=417792, initialPcmHashesEqual=True,
                  olderWorkerOnlyProofWasIncorrectlyAppliedToInitialEntry=True,
                  failedFullApplicationFrames=27251, failedFullApplicationStages=[1, 2],
                  failedFullApplicationAssertionsPassed=20, fullApplicationFailureRetained=True,
                  originalOrdinaryGuiAccepted=False, completeReplayAcceptance=False,
                  browserAcceptance=False, completeGame=False, nativeEquivalent=False,
                  previousPublishedCommit='59ac9c67b850ed0348fdc6d047b1cd80aa02ae79',
                  verifierSha256=SHA(Path(__file__).read_bytes()), bindings=bindings)
    if args.check:
        assert json.loads(args.output.read_bytes()) == result
    else:
        args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'bindings'}), flush=True)


if __name__ == '__main__':
    main()
