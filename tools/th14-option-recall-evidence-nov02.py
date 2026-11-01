"""Recompute the option-recall repair from native bytes and retained regressions."""
from pathlib import Path
import argparse, array, gzip, hashlib, importlib.util, json, struct

R = Path(__file__).resolve().parents[1]
SHA = lambda b: hashlib.sha256(b).hexdigest()


def evidence(home):
    home = home.resolve(strict=True)
    assert home.is_relative_to(R / 'artifacts/th14')
    bindings = {}

    def raw(path):
        path = path.resolve(strict=True)
        assert path.is_relative_to(R)
        data = path.read_bytes()
        bindings[path.relative_to(R).as_posix()] = dict(bytes=len(data), sha256=SHA(data))
        return data

    def load(path):
        return json.loads(raw(path))

    def module(name, path):
        raw(path)
        spec = importlib.util.spec_from_file_location(name, path)
        result = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(result)
        return result

    native_component = module('recall_retail_component', R / 'tools/th14-option-recall-native-nov02.py')
    retail = native_component.evidence()
    assert retail == load(home / 'retail-completion-recall.json')
    assert retail['cases'] == 84 and retail['realRetailCompletionAndRecallExecuted']
    # This diagnostic explicitly controls the two original threads. Retain its
    # protocol proof; a gameplay-field improvement does not accept natural timing.
    controlled_home = R / 'artifacts/th14/controlled-std-vm-return-nov02'
    controlled_tool = module('recall_controlled_std', R / 'tools/th14-controlled-std-vm-return-evidence-nov02.py')
    controlled = controlled_tool.evidence(controlled_home)
    assert controlled == load(controlled_home / 'controlled-verified.json')
    for name, binding in controlled['bindings'].items():
        assert SHA(raw(R / name)) == binding['sha256']

    B = home / 'candidate/observer-build.json'
    build = load(B)
    baseline_path = R / 'artifacts/th14/controller-polar-production-nov01/production-core/observer-build.json'
    baseline = load(baseline_path)
    assert baseline['wasmSha256'] == 'af9ec42926395595779d2744868a5cbff22cb9ddb39588e1a76265c395cffd9a'
    assert build['compiled'] and build['isolatedPrototypeOnly'] and build['all141ObjectsRecompiledForChangedClassLayout']
    assert build['optionRecallDeliveredOnlyByCompletionEffect']
    assert SHA(raw(B.parent / 'observer.wasm')) == build['wasmSha256']
    changed = []
    for inventory in ['sourceHashes', 'headerHashes']:
        assert build[inventory].keys() == baseline[inventory].keys()
        for name, digest in build[inventory].items():
            assert SHA(raw(Path(build['sourceSnapshotRoot']) / name)) == digest
            if digest != baseline[inventory][name]:
                changed.append(name)
    assert sorted(changed) == ['th12_web/cpp/game/GameBattle.cpp', 'th12_web/cpp/game/GameBattle.hpp']
    assert len(build['objectBindings']) == 141
    for row in build['objectBindings']:
        assert SHA(raw(Path(row['path']))) == row['sha256']
    for name, digest in build['fixtureDependencyHashes'].items():
        assert SHA(raw(Path(name))) == digest

    N = controlled_home / 'native'
    old, new = home / 'baseline-controlled-std', home / 'controlled-std'
    driver = R / 'tools/th14-compare-native-campaign-retained-camera-nov01.mjs'
    for tag, model, expected in [('baseline-controlled-std', old, baseline), ('controlled-std', new, build)]:
        terminal = load(home / (tag + '-process-end.json'))
        start = load(home / (tag + '-process-start.json'))
        report = load(model / 'report.json')
        assert terminal['exitCode'] == 1 and terminal['guardStop'] is None and not terminal['strictPassed']
        assert start['driverSha256'] == report['comparisonToolSha256'] == SHA(raw(driver))
        assert report['callbacks'] == 26000 and report['wasmSha256'] == expected['wasmSha256']
        assert report['diagnosticPrefixOnly'] and report['hostNormalBoundaryMode'] == 'none'
        assert report['normalBoundaryObservation'] is report['normalVmBoundaryObservation'] is None
        assert report['noNativePublicationValuesProvidedToEngine'] and report['noPerFrameStateOverrides']
        assert '--scene-vm-boundary-observation' not in start['argv']
        assert len(raw(N / 'selected-state.u32')) == 26000 * 128
        assert raw(N / 'selected-state.u32') == raw(model / 'selected-state.u32')
        camera = raw(N / 'world-camera.raw')
        assert len(camera) == 26000 * 0x124
        expected_camera = array.array('I', (struct.unpack_from('<I', camera, n * 0x124 + offset)[0]
            for n in range(26000) for offset in [*range(0, 88, 4), 0x104, 0x108, 0x10c])).tobytes()
        assert expected_camera == raw(model / 'portable-camera.u32')
        assert raw(N / 'hud-score.u32') == raw(model / 'portable-hud.u32')
    decoder = module('recall_vm303', R / 'tools/th14-hud-completion-evidence-check-oct25.py')
    fields = load(new / 'live-report.json')['fields']
    assert fields == load(old / 'live-report.json')['fields'] and len(fields) == 303
    before, after, repaired, rows_total = [], [], [], 0
    for path in sorted(N.glob('live-vms-callback-*.json')):
        callback = int(path.stem.rsplit('-', 1)[1])
        rows = load(path)['rows']
        previous = load(old / f'portable-live-{callback}.json')
        current = load(new / f'portable-live-{callback}.json')
        blobs = [bytes.fromhex(row['rawVmHex']) for row in rows]
        handles = {struct.unpack_from('<I', blob, 0x570)[0]: struct.unpack_from('<I', blob, 0x540)[0] for blob in blobs}
        assert len(handles) == len(rows)
        assert [row['handle'] for row in rows] == [row[0] for row in previous] == [row[0] for row in current]
        for row, blob, a, b in zip(rows, blobs, previous, current, strict=True):
            want = decoder.vm_words(blob, handles)
            assert len(want) == len(a) == len(b) == 303
            for field, (native_value, old_value, new_value) in enumerate(zip(want, a, b, strict=True)):
                detail = dict(callback=callback, handle=row['handle'], file=row['file'], script=row['script'],
                              field=fields[field], native=native_value)
                if old_value != native_value:
                    before.append(dict(**detail, portable=old_value))
                if new_value != native_value:
                    assert (row['file'], row['script'], fields[field], new_value) == (8, 149, 'worldZ', 0)
                    after.append(dict(**detail, portable=new_value))
                if old_value != new_value:
                    assert (callback, row['file'], row['script'], native_value, old_value, new_value) == (
                        22335, 9, 11, 1069547520, 1068320686, 1069547520)
                    assert fields[field] in ['scale.start0', 'scale.start1']
                    repaired.append(dict(**detail, before=old_value, after=new_value))
        rows_total += len(rows)
    assert len(before) == 14 and len(after) == 6 and len(repaired) == 8
    assert len({row['handle'] for row in repaired}) == 4
    schema = module('recall_combat_schema', R / 'tools/th14-combat-pool-readonly-v3-oct25.py')
    index = load(N / 'combat-pool-index.json')
    assert index['fields'] == json.loads(json.dumps(schema.SCHEMA))
    for entry in index['snapshots']:
        compressed = raw(N / 'combat-pools' / entry['file'])
        assert SHA(compressed) == entry['sha256']
        observed = json.loads(gzip.decompress(compressed))
        for model in [old, new]:
            got = load(model / f"combat-{entry['callback']}.json")
            assert (observed['callback'], observed['stage'], observed['stageFrame']) == (got['callback'], got['stage'], got['stageFrame'])
            for family, layout in index['fields'].items():
                expected = [[row['slot'] if offset is None else struct.unpack_from(
                    '<H' if family == 'bullets' and name == 'state' else '<I', bytes.fromhex(row['rawHex']), offset)[0]
                    for name, offset in layout] for row in observed['original'][family]]
                assert expected == got['rows'][family]
    publications = [json.loads(line) for line in raw(N / 'allocation-events.jsonl').decode().splitlines()]
    for model in [old, new]:
        got = load(model / 'portable-allocations-initial-through-1000.json')
        assert [(row['handle'], row['file'], row['script']) for row in publications] == [(row['handle'], row['file'], row['script']) for row in got]

    full = home / 'full-regressions'
    end = load(full / 'end.json')
    assert end['allCasesActuallyExecuted'] and end['strictPasses'] == end['independentPasses'] == 11
    cases = []
    for case in end['results']:
        path = full / case['key']
        plan = load(path / 'plan.json')
        terminal = load(path / 'process-end.json')
        verified = load(path / 'raw-verified.json')
        assert case['strictPassed'] and case['independentVerifierExitCode'] == 0
        assert terminal['exitCode'] == 0 and terminal['guardStop'] is None
        assert plan['buildSha256'] == SHA(raw(B)) and verified['wasmSha256'] == build['wasmSha256']
        assert verified['verifiedFiniteEvidence'] and verified['originalNaturalReplayEndObserved'] and not verified['diagnosticPrefixOnly']
        for name, binding in verified['bindings'].items():
            assert SHA(raw(R / name)) == binding['sha256']
        assert sum(p.stat().st_size for p in path.rglob('*') if p.is_file()) <= 128 * 1024**2
        cases.append(dict(key=case['key'], callbacks=case['callbacks'], vmRows=verified['vm303Rows'],
                          combatCheckpoints=verified['combatCheckpoints'], strictAndIndependentPassed=True))
    assert sum(case['callbacks'] for case in cases) == 1178575
    integrated = None
    if (home / 'integration-plan.json').exists():
        plan = load(home / 'integration-plan.json')
        assert plan['testedBuildSha256'] == SHA(raw(B)) and len(plan['changes']) == 2
        assert {row['path'] for row in plan['changes']} == {'runtimes/th12/' + name for name in changed}
        for row in plan['changes']:
            assert SHA(raw(R / row['path'])) == row['after'] and row['before'] != row['after']
        for inventory in ['sourceHashes', 'headerHashes']:
            for name, digest in build[inventory].items():
                path = R / 'runtimes/th12' / name
                if name.endswith('/ResourceCrypt.cpp'):
                    path = R / 'tools/tmp/github-source-release/runtimes/th12' / name
                assert SHA(raw(path)) == digest
        integrated = dict(allProductionSourceAndHeadersEqualTestedSnapshot=True, sourceFilesChanged=2,
                          noAdditionalGameplayChangeAfterTesting=True, testedWasmRetained=True)
    assert SHA(raw(R / 'artifacts/th14/vm-return-worker-oct29/work-state.json')) == '2236db52bee27439486e69216333cd88ddc27d1dcc28233f87bacdcaadc1f33c'
    assert SHA(raw(R / 'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp')) == 'a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45'
    return dict(verifiedFiniteOptionRecallRepair=True, previousProductionCoreCommit='85811ecb5f4a6e4bb3a2add3c0c6aebb31813dd6',
                candidateWasmSha256=build['wasmSha256'], changedEngineFiles=changed, all141ObjectsRecompiled=True,
                nativeComponentCases=84, diagnosticCallbacks=26000, vmRows=rows_total, vmFields=303,
                beforeDifferentWords=14, afterDifferentWords=6, correctedFields=repaired, remainingDifferences=after,
                allSelected32Camera25Hud2AndInitialPublicationsExact=True, allCapturedCombatWordsExact=True,
                combatCheckpoints=len(index['snapshots']), initialPublications=len(publications),
                noAdditionalModelClockHooks=True, noNativeObservedGameValuesProvidedToEngine=True,
                fullRegressions=cases, fullRegressionCallbacks=1178575, allElevenStrictAndIndependentPassed=True,
                productionIntegration=integrated,
                knownOldInitializationRngFailureClosed=False, diagnosticStrictPassed=False,
                controlledOriginalThreadTimingDeclared=True, ordinaryIndependentTimingAccepted=False,
                fullApplicationsAfterRepairAccepted=False, newBrowserUiAccepted=False,
                originalWholePixelsOrPcmAccepted=False, completeGame=False, nativeEquivalent=False,
                bindings=bindings, verifierSha256=SHA(Path(__file__).read_bytes()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(R / 'artifacts/th14') or output.is_relative_to(R / 'docs/porting')
    result = evidence(args.case)
    if args.check:
        assert json.loads(output.read_bytes()) == result
    else:
        output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(json.dumps({key: value for key, value in result.items() if key not in ['bindings', 'fullRegressions', 'correctedFields', 'remainingDifferences']}))
