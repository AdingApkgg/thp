"""Verify instruction-level initialization delivery without relaxing raw VM gates."""
from pathlib import Path
import argparse, copy, hashlib, importlib.util, json, struct

R = Path(__file__).resolve().parents[1]
SHA = lambda data: hashlib.sha256(data).hexdigest()
H = R / 'artifacts/th14/nested-initialization-checkpoint-nov02'
B = R / 'artifacts/th14/nested-instruction-reimub-v2-nov02'
REGULAR = R / 'artifacts/th14/nested-instruction-regular-regressions-nov02'


def evidence(require_integrated=False):
    bindings = {}
    checked = {}

    def raw(path):
        path = path.resolve(strict=True)
        assert path.is_relative_to(R)
        data = path.read_bytes()
        bindings[path.relative_to(R).as_posix()] = dict(bytes=len(data), sha256=SHA(data))
        return data

    def load(path):
        return json.loads(raw(path))

    def check_table(table):
        for name, expected in table.items():
            path = (R / name).resolve(strict=True)
            assert path.is_relative_to(R)
            stat = path.stat()
            identity = (stat.st_size, stat.st_mtime_ns)
            if name not in checked:
                data = raw(path)
                assert len(data) == expected['bytes'] and SHA(data) == expected['sha256'], name
                checked[name] = (identity, expected)
            else:
                assert checked[name] == (identity, expected), name

    controlled = load(B / 'controlled-verified.json')
    raw_proof = load(B / 'controlled-candidate-v2-raw-verified.json')
    check_table(controlled['bindings'])
    check_table(raw_proof['bindings'])
    assert controlled['verifiedControlledOriginalNestedInstructionBoundary']
    assert controlled['capturedCallbacks'] == raw_proof['callbacks'] == 34000
    assert controlled['targetScriptOffset'] == 0x9c and controlled['originalMainPc'] == 0x4700a3
    assert controlled['originalNestedFactory'] == 0x47ee90
    assert controlled['startupFirstChanceNoticesRetained'] == 10
    assert not controlled['coldStartupEquivalenceAccepted'] and not controlled['startupExceptionCauseClassified']
    assert not controlled['ordinaryIndependentThreadTimingAcceptance']
    assert raw_proof['verifiedFiniteEvidence'] and raw_proof['allSelected32Equal']
    assert raw_proof['allVm303AndRegistryOrderEqual'] and raw_proof['allCapturedCombatWordsEqual']
    assert raw_proof['controlledInstructionObservationSha256'] == SHA(raw(B / 'controlled-verified.json'))
    assert raw_proof['vm303Rows'] == 956 and raw_proof['combatCheckpoints'] == 322
    assert raw_proof['orderedPublications'] == 3274
    assert not raw_proof['ordinaryIndependentThreadTimingAcceptance']
    assert sum(s['callback'] > controlled['precedingPlayerCallbacks'] for s in raw_proof['vm303Snapshots']) >= 3
    notices = load(B / 'startup-notice-classification.json')
    assert notices['retainedRecords'] == 10 and not notices['coldStartupAccepted']
    assert len(notices['negativeControls']) == 4 and all(x['rejected'] for x in notices['negativeControls'])
    notice_tool = R / 'tools/th14-controlled-nested-instruction-prefix-evidence-nov02.py'
    raw(notice_tool)
    spec = importlib.util.spec_from_file_location('instruction_notice_gate', notice_tool)
    notice_gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(notice_gate)
    original_notices = load(B / 'native/report.json')['debugErrors']
    first_player_ns = load(B / 'native/untouched-first-player.json')['hostMonotonicNs']
    assert notice_gate.verify_startup_notices(original_notices, first_player_ns) == 10
    for key, value in [('firstChance', 0), ('callbacks', 1), ('code', 0xc0000005), ('hostMonotonicNs', first_player_ns)]:
        altered = copy.deepcopy(original_notices)
        altered[0][key] = value
        rejected = False
        try:
            notice_gate.verify_startup_notices(altered, first_player_ns)
        except AssertionError:
            rejected = True
        assert rejected, key
    old = load(B / 'controlled-baseline-v2-end.json')
    new = load(B / 'controlled-candidate-v2-end.json')
    assert old['exitCode'] == 1 and old['guardStop'] is None and not old['strictPassed']
    assert old['selectedDifferenceCounts'] == {'21': 3287, '22': 95, '26': 1}
    assert old['vmDifferentWords'] == 1823 and old['combatDifferentWords'] == 135
    assert old['modelClock']['delivered'] == 0 and old['modelClock']['failed'] == 0
    assert new['exitCode'] == new['independentVerifierExitCode'] == 0 and new['guardStop'] is None
    assert new['strictPassed'] and new['selectedDifferenceCounts'] == {}
    assert new['vmDifferentWords'] == new['combatDifferentWords'] == 0
    assert new['modelClock']['delivered'] == 1 and new['modelClock']['failed'] == 0

    candidate = load(H / 'candidate-v1/observer-build.json')
    regular = load(H / 'regular-core/observer-build.json')
    previous = load(R / 'artifacts/th14/rgb-acceleration-stack-nov02/candidate-v5/observer-build.json')
    assert candidate['objectBindings'] == regular['objectBindings'] and len(regular['objectBindings']) == 141
    assert candidate['sourceHashes'] == regular['sourceHashes'] and candidate['headerHashes'] == regular['headerHashes']
    assert candidate['wasmSha256'] == 'f5400b63684bacde9526e4f8ca3fb447153384e748dfe16eed6cf4c584aacfc7'
    assert regular['wasmSha256'] == 'dc7e2a677d60371166cbb03352f566fd86278dd8a8dfe13879dc968ed5692ccc'
    assert raw_proof['wasmSha256'] == candidate['wasmSha256']
    assert SHA(raw(H / 'candidate-v1/observer.wasm')) == candidate['wasmSha256']
    assert SHA(raw(H / 'regular-core/observer.wasm')) == regular['wasmSha256']
    assert regular['noNewFixtureApiAdded'] and regular['all141RecompiledInParent']
    source = Path(regular['sourceSnapshotRoot'])
    changed = []
    for name, digest in {**regular['sourceHashes'], **regular['headerHashes']}.items():
        assert SHA(raw(source / name)) == digest
        if digest != {**previous['sourceHashes'], **previous['headerHashes']}[name]:
            changed.append(Path(name).name)
            if require_integrated:
                assert raw(R / 'runtimes/th12' / name) == raw(source / name)
    assert sorted(changed) == ['AnmInterpreter.cpp', 'AnmManager.hpp', 'AnmVm.hpp']
    for row in regular['objectBindings']:
        assert SHA(raw(Path(row['path']))) == row['sha256']
    for report in [candidate, regular]:
        for path, digest in report['fixtureDependencyHashes'].items():
            assert SHA(raw(Path(path))) == digest
    syntax = load(H / 'syntax-checks/report.json')
    assert syntax['passed'] and len(syntax['checks']) == 12
    assert all(x['exitCode'] == 0 for x in syntax['checks'])
    natural = load(REGULAR / 'end.json')
    plan = load(REGULAR / 'plan.json')
    assert (natural['casesCompleted'], natural['strictPasses'], natural['independentPasses'], natural['callbacks']) == (15, 15, 15, 1571493)
    assert plan['buildSha256'] == SHA(raw(H / 'regular-core/observer-build.json'))
    for row in natural['results']:
        assert row['strictPassed'] and row['exitCode'] == row['independentVerifierExitCode'] == 0
        assert row['guardStop'] is row['independentGuardStop'] is None
        proof = load(R / row['caseDirectory'] / 'raw-verified.json')
        assert proof['verifiedFiniteEvidence'] and proof['wasmSha256'] == regular['wasmSha256']
        check_table(proof['bindings'])

    # Independently retain all five unresolved script149 words. This sample
    # remains a strict failure even though its RNG and combat differences fell.
    vm_tool = R / 'tools/th14-hud-completion-evidence-check-oct25.py'
    raw(vm_tool)
    spec = importlib.util.spec_from_file_location('instruction_native_vm', vm_tool)
    vm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vm)
    native = H / 'native'
    model = H / 'controlled-candidate-v2'
    assert raw(native / 'selected-state.u32') == raw(model / 'selected-state.u32')
    fields = load(model / 'live-report.json')['fields']
    differences = []
    for path in sorted(native.glob('live-vms-callback-*.json')):
        callback = int(path.stem.rsplit('-', 1)[1])
        rows = load(path)['rows']
        blobs = [bytes.fromhex(x['rawVmHex']) for x in rows]
        handles = {struct.unpack_from('<I', b, 0x570)[0]: struct.unpack_from('<I', b, 0x540)[0] for b in blobs}
        actual = load(model / f'portable-live-{callback}.json')
        assert len(handles) == len(rows) == len(actual)
        assert [r['handle'] for r in rows] == [r[0] for r in actual]
        for row, blob, portable in zip(rows, blobs, actual, strict=True):
            expected = vm.vm_words(blob, handles)
            for index, (a, b) in enumerate(zip(expected, portable, strict=True)):
                if a != b:
                    assert (row['file'], row['script'], fields[index], b) == (8, 149, 'worldZ', 0)
                    differences.append(dict(callback=callback, file=8, script=149, field='worldZ'))
    assert len(differences) == 5 and sum(d['callback'] < 22257 for d in differences) == 3
    retained = load(H / 'controlled-candidate-v2-end.json')
    assert not retained['strictPassed'] and retained['vmDifferentWords'] == 5
    assert retained['selectedDifferenceCounts'] == {} and retained['combatDifferentWords'] == 0
    # Keep the exact executed comparator; the public copy only removes the
    # additional CR introduced by Windows newline translation.
    executed_comparator = raw(H / 'comparison-tool-v2-used.mjs')
    public_comparator = raw(R / 'tools/th14-compare-controlled-nested-instruction-nov02.mjs')
    assert executed_comparator.replace(b'\r\r\n', b'\r\n') == public_comparator
    assert load(model / 'report.json')['comparisonToolSha256'] == SHA(executed_comparator)
    for name, expected in [
        ('runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp', 'a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45'),
        ('artifacts/th14/vm-return-worker-oct29/work-state.json', '2236db52bee27439486e69216333cd88ddc27d1dcc28233f87bacdcaadc1f33c')]:
        assert SHA((R / name).read_bytes()) == expected
    for name, (identity, _) in checked.items():
        stat = (R / name).stat()
        assert identity == (stat.st_size, stat.st_mtime_ns), name
    return dict(verifiedFiniteInstructionInitializationRepair=True,
                productionIntegrated=require_integrated, changedFiles=sorted(changed),
                previousCoreCommit='54cbc0cd05b5db6d8257ffa14dc1dcaf407a8754',
                coreWasmSha256=regular['wasmSha256'], controlledFixtureWasmSha256=candidate['wasmSha256'],
                all141CoreObjectsRecompiled=True, controlledAndRegular141ObjectsIdentical=True,
                regularFixtureHasNoNewApi=True, controlledReimubCallbacks=34000,
                controlledVm303Rows=956, controlledCombatCheckpoints=322,
                baselineSelectedDifferences=old['selectedDifferenceCounts'],
                baselineVmDifferentWords=1823, baselineCombatDifferentWords=135,
                candidateStrictAndIndependentPassed=True, candidateVmAndCombatDifferentWords=0,
                regularNaturalStrictAndIndependentPasses=15, regularNaturalCallbacks=1571493,
                originalStartupFirstChanceNoticesRetained=10, coldStartupAccepted=False,
                startupExceptionCauseClassified=False, startupNoticeNegativeControlsRejected=4,
                reimuaStrictPrefixAccepted=False, reimuaUnresolvedVmWords=5,
                reimuaUnresolvedFields=differences, nativeValuesProvidedToEngine=False,
                ordinaryOriginalGuiAccepted=False, independentSchedulingAccepted=False,
                wholeOriginalPixelsOrPcmAccepted=False, currentNewCoreFullApplicationAccepted=False,
                browserAccepted=False, naturalModes=30, allStageEntryModes=27,
                completeGame=False, nativeEquivalent=False, bindings=bindings,
                verifierSha256=SHA(Path(__file__).read_bytes()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-integrated', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(R / 'artifacts/th14') or output.is_relative_to(R / 'docs/porting')
    result = evidence(args.require_integrated)
    if args.check:
        assert json.loads(output.read_bytes()) == result
    else:
        output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(json.dumps({k: v for k, v in result.items() if k not in ['bindings', 'reimuaUnresolvedFields']}))
