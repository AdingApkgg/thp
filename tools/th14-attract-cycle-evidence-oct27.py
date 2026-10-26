"""Check current Application attract flows and preserve backend pixel failures."""
from pathlib import Path
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda raw: hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    home = args.home.resolve()
    assert home.is_relative_to(ROOT / 'artifacts/th14')
    bindings = {}

    def digest(path):
        with path.open('rb') as stream:
            value = hashlib.file_digest(stream, 'sha256').hexdigest()
        bindings[path.relative_to(ROOT).as_posix()] = dict(bytes=path.stat().st_size, sha256=value)
        return value

    def load(path):
        digest(path)
        return json.loads(path.read_bytes())

    scenario = ROOT / 'runtimes/th12/th12_web/tests/fixtures/th14-native-application-attract-cycle-oct27.json'
    definition = load(scenario)
    assert digest(scenario) == digest(home / 'scenario-at-start.json')
    assert len(definition['actions']) == 13 and all(not a.get('held', 0) and not a.get('pause', 0) for a in definition['actions'])
    runs = {}
    builds = {}
    folders = dict(webgpu=home / 'webgpu-after-storage', gles=home / 'gles')
    for backend, folder in folders.items():
        run = load(folder / 'report.json')
        build_home = home / ('build-' + backend)
        build = load(build_home / 'build.json')
        assert run['backend'] == build['backend'] == backend and run['completed'] and not run['error']
        assert run['actualProductionApplicationAndDevices'] and run['platformClockAndIoDeclared']
        assert run['physicalAudioDevicesOpened'] == 0 and not run['appUiControlled'] and not run['browserRun']
        assert run['pendingAsyncCallbacks'] == 0
        context = ROOT / ('tools/th14-native-webgpu-context.py' if backend == 'webgpu' else 'tools/th14-native-gles-context.py')
        assert run['hostToolSha256'] == digest(context)
        assert run['initialSave'] == run['finalSave'] == {}
        assert run['scenarioSha256'] == digest(scenario)
        assert run['toolSha256'] == digest(folder / 'run-tool.py') == digest(ROOT / 'tools/th14-native-application.py')
        assert run['buildReportSha256'] == digest(build_home / 'build.json')
        assert run['wasmSha256'] == build['wasmSha256'] == digest(build_home / 'application.wasm')
        for path, row in build['sourceBindings'].items():
            assert digest(ROOT / path) == row['sha256'], path
        for row in build['coreObjects']:
            assert digest(Path(row['path'])) == row['sha256']
        assert len(build['coreObjects']) == 141 and len(build['newObjects']) == 5
        for name, value in build['newObjects'].items():
            assert digest(build_home / name) == value
        assert len(run['checks']) == 30 and all(c['passed'] and c['actual'] == c['expected'] for c in run['checks'])
        assert len(run['actions']) == 13 and all(a['held'] == a['pause'] == 0 for a in run['actions'])
        for index, stage in [(1, 3), (5, 4), (9, 1)]:
            assert run['actions'][index]['state'][:2] == [1, stage]
            assert run['actions'][index + 1]['state'][6] == 241
        for index in [4, 8, 12]:
            state = run['actions'][index]['state']
            assert state[0] == 0 and state[3:6] == [1, 0, 2] and state[19] == 1
        assert run['frames'] <= 27000 and len(run['captures']) == 7
        assert run['archiveSha256'] == '57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233'
        assert run['metadataEpochAtFrameZero'] == 1793037600
        runs[backend] = run
        builds[backend] = build
    a, b = runs['webgpu'], runs['gles']
    assert a['frames'] == b['frames'] and a['actions'] == b['actions'] and a['rows'] == b['rows'] and a['checks'] == b['checks']
    assert a['pcmFrames'] == b['pcmFrames'] and a['pcmSha256'] == b['pcmSha256']
    assert builds['webgpu']['coreObjects'] == builds['gles']['coreObjects']
    diagnostic = load(home / 'pair-diagnostic.json')
    assert not diagnostic['runningPrefixOnly'] and diagnostic['completedRuns'] == ['gles', 'webgpu']
    assert diagnostic['verifierSha256'] == digest(ROOT / 'tools/th14-application-render-pair-check.py')
    assert diagnostic['pairedImages'] == 7 and diagnostic['sharedCompletedActions'] == 13
    assert diagnostic['allSharedActionStatesEqual'] and not diagnostic['stateDifferences']
    comparisons = []
    for left, right in zip(a['captures'], b['captures']):
        assert left['label'] == right['label'] and left['frame'] == right['frame']
        buffers = []
        for backend, row in [('webgpu', left), ('gles', right)]:
            path = folders[backend] / row['file']
            assert Path(row['file']).name == row['file'] and digest(path) == row['sha256']
            raw = path.read_bytes()
            assert len(raw) == 640 * 480 * 4
            buffers.append(raw)
        indices = [i for i, (x, y) in enumerate(zip(*buffers)) if x != y]
        first = indices[0] if indices else None
        comparisons.append(dict(label=left['label'], frame=left['frame'], bytes=len(buffers[0]),
            differentBytes=len(indices), differentPixels=len({i // 4 for i in indices}),
            firstDifference=None if first is None else dict(x=first // 4 % 640, y=first // 4 // 640,
                channel='BGRA'[first % 4], webgpu=buffers[0][first], gles=buffers[1][first])))
    assert comparisons == diagnostic['pairs']
    pixels_equal = all(not row['differentBytes'] for row in comparisons)
    assert pixels_equal == diagnostic['allPairedCapturedBuffersEqual']
    failed = load(home / 'webgpu/report.json')
    limit = load(home / 'webgpu/storage-limit.json')
    assert not failed['completed'] and failed['error'].startswith("RuntimeError('TH14 capture storage budget exceeded")
    assert failed['frames'] == 11681 and limit['storageBudgetExceeded'] and limit['freeBytes'] < limit['minimumFreeBytes']
    assert [r for r in a['rows'] if r['frame'] <= failed['frames']] == failed['rows']
    regression = load(home / 'pair-checker-regression.json')
    assert regression['framesPerBackend'] == 123412 and regression['pairedImages'] == 8
    assert regression['allPairedCapturedBuffersEqual'] and regression['allSharedActionStatesEqual']
    for stem in ['storage-compression', 'frozen-compression']:
        plan = load(home / (stem + '-plan.json'))
        verified = load(home / (stem + '-verified.json'))
        assert verified['allContentHashesUnchanged'] and verified['allPathsUnchanged']
        for row in plan['files']:
            assert digest(ROOT / row['path']) == row['sha256']
    result = dict(verifiedFiniteAttractFlows=True, framesPerBackend=a['frames'], assertionsPerBackend=30,
        completedActions=13, observedNaturalDemoStages=[3, 4, 1], allActionsHeldNoKeys=True, threeNaturalTitleReturns=True,
        same141CoreObjects=True, currentBgrxHeaderBound=True, pairedJournalRows=len(a['rows']),
        allJournalAndActionStatesEqual=True, pcmFramesPerBackend=a['pcmFrames'], silentPcmSinkHashEqual=True,
        rawPcmIndependentlyRetained=False, pairedImages=7, comparedImageBytes=7 * 640 * 480 * 4,
        pixelEqualityPassed=pixels_equal, imageDifferences=comparisons, differingChannelsRetained=True,
        originalGpuCapacityFailureRetained=True, onlyFailedGpuRunRepeated=True,
        pairCheckerPositiveRegressionImages=8, productionGameplayChanged=False,
        originalApplicationPixelsEqualNotAsserted=True, originalOrdinaryUiAcceptance=False,
        browserAcceptance=False, completeGame=False, nativeEquivalent=False,
        verifierSha256=SHA(Path(__file__).read_bytes()), bindings=bindings,
        scope='Current actual C++ Application on declared native platforms, intact archive and no keys. Both terminal flows and exact state/PCM hashes checked; every retained pixel difference stays a failing equality gate. Earlier capacity failure preserved. No original ordinary UI/pixels/PCM, browser, physical devices or whole-game acceptance.')
    output = args.output.resolve()
    assert output.is_relative_to(ROOT / 'artifacts/th14') or output.is_relative_to(ROOT / 'docs/porting')
    if args.check:
        assert json.loads(output.read_bytes()) == result
    else:
        output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(json.dumps({key: result[key] for key in ['verifiedFiniteAttractFlows', 'framesPerBackend', 'pairedJournalRows', 'pairedImages', 'pixelEqualityPassed']}))
    assert pixels_equal, 'Actual Application image differences remain; finite flow verification does not waive them'


if __name__ == '__main__':
    main()
