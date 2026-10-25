"""Recompute Scene scheduling evidence while preserving full-run VM failures."""
import argparse
import array
import collections
import gzip
import hashlib
import importlib.util
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT/'artifacts/th14/stage-item-retirement-oct25'
SHA = lambda data: hashlib.sha256(data).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def verify():
    bindings = {}

    def read(path):
        data = path.read_bytes()
        bindings[path.relative_to(ROOT).as_posix()] = dict(bytes=len(data), sha256=SHA(data))
        return data

    load = lambda path: json.loads(read(path))
    build_path = HOME/'curve-origin-observer-oct26/observer-build.json'
    build = load(build_path)
    assert SHA(read(build_path.parent/'observer.wasm')) == build['wasmSha256']
    for row in build['objectBindings']:
        assert SHA(Path(row['path']).read_bytes()) == row['sha256']
    for path, digest in build['fixtureDependencyHashes'].items():
        current = Path(path)
        retained = ROOT/'artifacts/th14/shared-observer-source-cache'/(digest+'.bin')
        assert (current.exists() and SHA(current.read_bytes()) == digest) or (retained.exists() and SHA(retained.read_bytes()) == digest)
    vm = module('vm_fields', ROOT/'tools/th14-hud-completion-evidence-check-oct25.py')
    schema = module('combat_fields', ROOT/'tools/th14-combat-pool-readonly-v3-oct25.py')
    summaries = []
    for mode, native_name, model_name, expected_callbacks, expected_vm_differences in [
            ('reimua-hard', 'retail-reimua-hard-callback-rng-hardware-oct26',
             'reimua-hard-scene-handoff-full-oct26', 96103, 6),
            ('reimua-lunatic', 'retail-reimua-lunatic-exit-boundary-hardware-oct26',
             'reimua-lunatic-scene-handoff-full-oct26', 86751, 5)]:
        native, model = ROOT/'artifacts/th14'/native_name, HOME/model_name
        original, reported = load(native/'report.json'), load(model/'report.json')
        assert original['callbacks'] == reported['callbacks'] == expected_callbacks
        assert original['observedForcedReplayEndMenu'] and original['childExited'] and not original['error']
        assert original['hardwareBreakpointsOnly'] and original['instructionBytesPatched'] == original['rngOrCounterWrites'] == 0
        assert not original['inputInjected'] and original['gameStateWordWrites'] == 1
        assert original['caseInitialization']['attractBitClearOnly']
        assert reported['wasmSha256'] == build['wasmSha256']
        assert reported['comparisonToolSha256'] == SHA(read(ROOT/'tools/th14-compare-native-campaign.mjs'))
        assert not reported['diagnosticPrefixOnly'] and reported['noPerFrameStateOverrides']
        assert reported['noNativePublicationValuesProvidedToEngine']
        assert reported['allPortableBulletOpcodesSupported'] and not reported['portableUnsupportedBulletObservations']
        state = read(native/'selected-state.u32')
        assert len(state) == expected_callbacks*128 and state == read(model/'selected-state.u32')
        assert SHA(state) == original['selectedSha256'] == reported['selectedSha256']
        camera = read(native/'world-camera.raw')
        assert len(camera) == expected_callbacks*0x124
        offsets = [*range(0, 88, 4), 0x104, 0x108, 0x10c]
        expected = array.array('I', (struct.unpack_from('<I', camera, n*0x124+offset)[0]
                                    for n in range(expected_callbacks) for offset in offsets))
        assert expected.tobytes() == read(model/'portable-camera.u32')
        assert read(native/'hud-score.u32') == read(model/'portable-hud.u32')
        differences, snapshots = [], []
        for path in sorted(native.glob('live-vms-callback-*.json')):
            callback = int(path.stem.rsplit('-', 1)[1])
            rows, actual = load(path)['rows'], load(model/f'portable-live-{callback}.json')
            blobs = [bytes.fromhex(row['rawVmHex']) for row in rows]
            handles = {struct.unpack_from('<I', blob, 0x570)[0]: struct.unpack_from('<I', blob, 0x540)[0] for blob in blobs}
            assert len(handles) == len(rows)
            assert [row['handle'] for row in rows] == [row[0] for row in actual]
            expected = [vm.vm_words(blob, handles) for blob in blobs]
            for native_row, portable_row in zip(expected, actual, strict=True):
                assert len(native_row) == len(portable_row) == 303
                for word, (a, b) in enumerate(zip(native_row, portable_row, strict=True)):
                    if a != b:
                        differences.append((callback, word, native_row[2], native_row[3]))
            snapshots.append(dict(callback=callback, rows=len(rows), selectedWordsPerVm=303))
        live = load(model/'live-report.json')
        retained_differences = [row for s in live['snapshots'] for row in s['differences']]
        assert len(differences) == len(retained_differences) == expected_vm_differences
        assert not live['allLiveValuesEqual']
        assert all(row['field'] == 'worldZ' and row['file'] == 8 and row['script'] == 149 for row in retained_differences)
        assert len({row[1] for row in differences}) == 1
        index = load(native/'combat-pool-index.json')
        assert index['fields'] == json.loads(json.dumps(schema.SCHEMA))
        totals, nonempty = collections.Counter(), 0
        for entry in index['snapshots']:
            compressed = (native/'combat-pools'/entry['file']).read_bytes()
            assert SHA(compressed) == entry['sha256']
            source = json.loads(gzip.decompress(compressed))
            actual = json.loads((model/f"combat-{entry['callback']}.json").read_bytes())
            assert (source['callback'], source['stage'], source['stageFrame']) == (actual['callback'], actual['stage'], actual['stageFrame'])
            active = False
            for family, layout in index['fields'].items():
                expected = []
                for row in source['original'][family]:
                    blob = bytes.fromhex(row['rawHex'])
                    expected.append([row['slot'] if offset is None else struct.unpack_from(
                        '<H' if family == 'bullets' and name == 'state' else '<I', blob, offset)[0]
                        for name, offset in layout])
                assert expected == actual['rows'][family]
                totals[family] += len(expected); active |= bool(expected)
            nonempty += int(active)
        cutoff = original['anmPublicationTraceCutoffPlayerCallbacks']
        allocations = [json.loads(line) for line in read(native/'allocation-events.jsonl').decode().splitlines()]
        portable = load(model/f'portable-allocations-initial-through-{cutoff}.json')
        assert [(r['handle'], r['file'], r['script']) for r in allocations] == [(r['handle'], r['file'], r['script']) for r in portable]
        summaries.append(dict(mode=mode, callbacks=expected_callbacks, stagesObserved=original['recordedStages'],
                              allSelected32Equal=True, allCamera25Equal=True, allHud2Equal=True,
                              vm303Snapshots=snapshots, vm303Rows=sum(r['rows'] for r in snapshots),
                              registryOrderEqual=True, vmWordDifferences=expected_vm_differences,
                              remainingVmDifferenceScope=dict(file=8, script=149, field='worldZ'),
                              fullCapturedRunAccepted=False, combatCheckpoints=len(index['snapshots']),
                              nonemptyCombatCheckpoints=nonempty, combatRows=dict(totals),
                              allCapturedCombatWordsEqual=True, orderedInitialPublications=len(allocations),
                              publicationCutoffCallbacks=cutoff, sceneUpdateHandoffs=reported['sceneUpdateHandoffs']))
    # The old full baseline uses an older gameplay Wasm; bind that version
    # explicitly rather than implying an identical-build full A/B experiment.
    old = HOME/'reimua-hard-bullet-hit-full-oct26'
    old_report, old_camera = load(old/'report.json'), load(old/'camera-report.json')
    assert old_camera['counts'] == {'12': 18399}
    # The prefix A/B uses the SAME diagnostic Wasm and native input, differing
    # only in the host scheduler. Both VM failure reports remain false.
    probe = HOME/'camera-copy-probe-oct26'
    prefix = []
    for name in ['reimua-hard-prefix-56000', 'reimua-hard-cross-update-prefix-56000']:
        report, camera = load(probe/name/'report.json'), load(probe/name/'camera-report.json')
        prefix.append((report, camera))
    assert prefix[0][0]['wasmSha256'] == prefix[1][0]['wasmSha256']
    assert prefix[0][0]['nativeSelectedSha256'] == prefix[1][0]['nativeSelectedSha256']
    assert prefix[0][1]['counts'] == {'12': 933} and prefix[1][1]['allCameraWordsEqual']
    regressions = []
    for name, callbacks in [('sakuyaa-hard', 96682), ('reimub-normal', 122537)]:
        proof = load(HOME/(name+'-scene-handoff-regression-verified-oct26.json'))
        report = load(HOME/(name+'-scene-handoff-regression-oct26')/'report.json')
        assert proof['verifiedFiniteEvidence'] and proof['callbacks'] == callbacks
        assert not proof['diagnosticPrefixOnly']
        assert proof['allSelected32Equal'] and proof['allCamera25Equal'] and proof['allHud2Equal']
        assert proof['allVm303AndRegistryOrderEqual'] and proof['allCapturedCombatWordsEqual']
        assert proof['wasmSha256'] == build['wasmSha256']
        assert proof['comparisonToolSha256'] == report['comparisonToolSha256'] == SHA(read(ROOT/'tools/th14-compare-native-campaign.mjs'))
        regressions.append(dict(mode=name, callbacks=callbacks, independentlyVerifiedFiniteEvidence=True,
                                vm303Rows=proof['vm303Rows'], combatCheckpoints=proof['combatCheckpoints']))
    negative = load(HOME/'scene-handoff-negative-regression-oct26.json')
    assert [row['mode'] for row in negative] == ['hard', 'lunatic']
    assert all(row['strictVerifierExitCode'] == 1 and row['rejectedAtFullVmEquality'] and row['noPassingReportWritten'] for row in negative)
    handoff = summaries[0]['sceneUpdateHandoffs']
    assert len(handoff) == 1 and handoff[0]['stage'] == 5 and handoff[0]['precedingPlayerCallbacks'] == 54933
    native = ROOT/'artifacts/th14/retail-reimua-hard-callback-rng-hardware-oct26'
    copies = [json.loads(line) for line in read(native/'scene-camera-copy-events.jsonl').decode().splitlines()]
    boundaries = [json.loads(line) for line in read(native/'camera-boundary-events.jsonl').decode().splitlines()]
    scene = next(row for row in copies if row['stage'] == 5 and row['event'] == 'scene-camera-copy-before')
    previous = scene['lastMainCameraBoundary']
    next_camera = next(row for row in boundaries if row['hostMonotonicNs'] == handoff[0]['nextControllerCameraNs'])
    assert scene['hostMonotonicNs'] == handoff[0]['sceneCopyNs'] and previous['hostMonotonicNs'] == handoff[0]['drawCameraBoundaryNs']
    assert scene['pc'] == 0x40d435 and previous['pc'] == 0x4465a6 and next_camera['pc'] == 0x40dae9
    assert previous['event'] == 'world-perspective-right-written' and next_camera['event'] == 'controller-camera-published'
    assert scene['mainPhaseAtObservation'] == next_camera['mainPhaseAtObservation'] == 'update'
    assert previous['mainPhaseAtObservation'] == 'draw'
    assert previous['hostMonotonicNs'] < scene['hostMonotonicNs'] < next_camera['hostMonotonicNs']
    return dict(schema='th14/scene-camera-handoff/1', verifiedRetainedDifferences=True,
                sourceToolSha256=SHA(read(ROOT/'tools/th14-compare-native-campaign.mjs')),
                checkerSha256=SHA(Path(__file__).read_bytes()), wasmSha256=build['wasmSha256'],
                productionChanged=False, fullCases=summaries,
                passingRegressions=regressions, strictFailureRegressions=negative,
                historicalFullCameraBaseline=dict(callbacks=96103, differingWord12Callbacks=18399,
                                                  wasmSha256=old_report['wasmSha256'], identicalWasmToCurrent=False),
                identicalDiagnosticWasmPrefixControl=dict(callbacks=56000, beforeCameraWord12Differences=933,
                                                         afterCameraWordDifferences=0, wholeRunScope=False),
                bindings=bindings, limitations=['Known VM Z differences remain fatal to the strict full-run verifier.',
                                               'The scheduler uses observed timestamps and instruction boundaries, never native camera values.',
                                               'The synthetic stack component does not prove actual stack provenance or later lifecycle.',
                                               'No ordinary menu, actual GPU/PCM, browser persistence, all-mode or whole-game equivalence is proved.'],
                completeGame=False, nativeEquivalent=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = verify()
    output = ROOT/'docs/porting/th14-scene-handoff-verified-oct26.json'
    if args.check:
        assert json.loads(output.read_bytes()) == result
    else:
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(verifiedRetainedDifferences=True,
                         cases=[dict(mode=r['mode'], callbacks=r['callbacks'], vmWordDifferences=r['vmWordDifferences'],
                                     fullCapturedRunAccepted=r['fullCapturedRunAccepted']) for r in result['fullCases']])))


if __name__ == '__main__':
    main()
