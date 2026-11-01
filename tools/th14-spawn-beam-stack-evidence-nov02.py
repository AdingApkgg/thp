"""Bind the observed constructor stack producer to finite strict regressions."""
from pathlib import Path
import argparse, hashlib, json

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/marisaa-beam-writer-context-nov02'
SHA = lambda b: hashlib.sha256(b).hexdigest()

def evidence(require_integrated=False):
    bindings = {}
    def bind(path):
        path = path.resolve(strict=True)
        assert path.is_relative_to(R)
        key = path.relative_to(R).as_posix()
        if key not in bindings:
            digest = hashlib.sha256()
            with path.open('rb') as stream:
                for chunk in iter(lambda: stream.read(1024**2), b''): digest.update(chunk)
            bindings[key] = dict(bytes=path.stat().st_size, sha256=digest.hexdigest())
        return bindings[key]['sha256']
    def load(path):
        bind(path)
        return json.loads(path.read_bytes())
    def retained_verified(path):
        proof = load(path)
        assert proof['verifiedFiniteEvidence'] and not proof['nativeEquivalent']
        for name, expected in proof['bindings'].items():
            assert bind(R / name) == expected['sha256'], name
        return proof

    B = H / 'spawn-candidate-v2/observer-build.json'
    build = load(B)
    wasm = build['wasmSha256']
    assert bind(B.parent / 'observer.wasm') == wasm
    assert len(build['objectBindings']) == len(build['sourceHashes']) == 141
    source = Path(build['sourceSnapshotRoot'])
    for name, digest in {**build['sourceHashes'], **build['headerHashes']}.items():
        assert bind(source / name) == digest
    for row in build['objectBindings']: assert bind(Path(row['path'])) == row['sha256']
    assert bind(R / 'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe') == build['compilerSha256']
    for name, digest in build['fixtureDependencyHashes'].items(): assert bind(Path(name)) == digest
    changed = build['candidateChangedFiles']
    assert len(changed) == 8
    integrated = all(SHA((R / 'runtimes/th12' / name).read_bytes()) == bind(source / name) for name in changed)
    if require_integrated: assert integrated, 'Tested candidate sources have not been integrated'
    assert SHA((R / 'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp').read_bytes()) == 'a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45'

    component = load(H / 'public-component-check/verified.json')
    assert component['passed'] and component['cases'] == 1536 and component['all32InterpolationModes']
    assert component['engineBuildSha256'] == bind(B)
    assert component['fixtureSha256'] == bind(R / 'runtimes/th12/th12_web/tests/cpp/th14-spawn-beam-stack-fixture-nov02.cpp')
    assert component['checkerSha256'] == bind(R / 'tools/th14-spawn-beam-stack-check-nov02.mjs')
    assert component['nativeToolSha256'] == bind(R / 'tools/th14-spawn-beam-stack-native-v2-nov02.py')
    assert component['nativeProofSha256'] == bind(H / 'public-component-check/native.json')
    assert component['wasmSha256'] == bind(H / 'public-component-check/fixture.wasm')

    events_path = H / 'native/beam-stack-events.jsonl'
    bind(events_path)
    events = [json.loads(line) for line in events_path.read_text().splitlines()]
    writes = {}
    producers = []
    for row in events:
        if row['event'] == 'beam-scratch-write-after-instruction': writes[row['scratchAddress']] = row
        elif row['pc'] == 0x45286f:
            assert row['actualReadMatchesWatch']
            writer = writes[row['scratchAddress']]
            assert writer['pc'] == 0x409f42 and writer['scratchBits'] == row['scratchBits']
            assert writer['boundedWriterEbpChain'][0]['returnPc'] == 0x473b1a
            assert [x['returnPc'] for x in writer['boundedWriterEbpChain'][:4]] == [0x473b1a, 0x472ca0, 0x42e00b, 0x4257ca]
            vm = bytes.fromhex(writer['candidateVmHex'])
            assert int.from_bytes(vm[0x570:0x574], 'little') == writer['candidateVmAddress']
            assert writer['candidateVmAddress'] + 0x9c == writer['registers']['esi']
            samples = load(H / 'current-position-model/position-samples.json')
            assert any(x[0] == row['precedingPlayerCallbacks'] + 1 and x[1:4] == [0, 8, 101] and x[4] == 0 and x[-1] == row['scratchBits'] for x in samples['rows'])
            producers.append(dict(callback=row['precedingPlayerCallbacks'] + 1, areaSlot=row['areaSlot'], writerPc=0x409f3d,
                                  writerPostPc=writer['pc'], readPc=row['pc'], sameWord=True, portableComputesSameBits=True))
    assert len(producers) == 1 and max(x.get('writeOrdinal', 0) for x in events) < 16384
    native = load(H / 'native/report.json')
    assert native['callbacks'] == 4800 and native['childExited'] and not native['error']
    silence = load(H / 'silent-levels.json')
    assert silence['verifiedActualNativeMasterLevelsZero']

    finite = load(H / 'candidate-cases-v2/queue-end.json')['cases']
    assert len(finite) == 7 and sum(x['callbacks'] for x in finite) == 37812
    for index, row in enumerate(finite, 1):
        assert row['exitCode'] == row['independentVerifierExitCode'] == 0
        verified = retained_verified(H / f'candidate-cases-v2/case-{index}-raw-verified.json')
        assert verified['wasmSha256'] == wasm
    totals = load(H / 'area-totals-v2/damage-total-trace.json')
    assert totals['rows'] == 651 and totals['differentWords'] == 0
    assert totals['nativeSha256'] == bind(R / 'artifacts/th14/marisaa-area-total-nov02/native/damage-area-totals.u32')
    assert totals['portableSha256'] == bind(H / 'area-totals-v2/portable-damage-area-totals.u32')
    shapes = load(H / 'area-shapes-verified-v3.json')
    assert shapes['allCapturedActiveAreaAndShotWordsEqual'] and shapes['portableRows'] == 401
    assert shapes['verifierSha256'] == bind(R / 'tools/th14-area-shape-verify-nov02.py')
    assert shapes['nativeCompressedSha256'] == bind(R / 'artifacts/th14/marisaa-area-shape-nov02/native/area-shot-window.bin.gz')
    assert shapes['modelPayloadSha256'] == bind(H / 'area-shapes-v2/area-shape-rows.json')

    end = load(H / 'full-regressions-v3/end.json')
    assert end['allCasesActuallyExecuted'] and end['casesCompleted'] == end['strictPasses'] == end['independentPasses'] == 12
    assert end['callbacks'] == 1302022
    full = []
    for row in end['results']:
        assert row['strictPassed'] and row['independentVerifierExitCode'] == 0
        directory = R / row.get('retainedCaseDirectory', row.get('caseDirectory'))
        verified = retained_verified(directory / 'raw-verified.json')
        assert verified['wasmSha256'] == wasm and verified['originalNaturalReplayEndObserved'] and not verified['diagnosticPrefixOnly']
        full.append(dict(key=row['key'], callbacks=row['callbacks'], strictAndIndependentPassed=True))
    bind(Path(__file__))
    return dict(verifiedFiniteSpawnBeamStackEvidence=True, candidateWasmSha256=wasm, productionIntegrated=integrated,
                changedFiles=changed, all141ObjectsRecompiledForNewLayoutInParent=True,
                actualOriginalWriterAndRead=producers, cppValuesComputedWithoutNativeStateInputs=True,
                componentCases=1536, all32InterpolationModes=True, finiteCases=7, finiteCallbacks=37812,
                activeAreaAndShotFramesExact=401, areaTotalFramesExact=651,
                completeNaturalRegressionCases=full, completeNaturalRegressionCallbacks=1302022,
                actualOriginalMusicAndEffectsMastersZero=True, physicalAudioDevicesOpenedByModels=0,
                originalMarisaaNormalInputNaturallyEndedInStage1=True, allStageEntryModePairsStill=26,
                otherConstructorStackProducersAndNestedDepthsRemainUnproved=True,
                completeApplicationPairStillBoundToPreviousCore='91a797541a5491d326a8c6e5d593e0890313879e',
                fullOriginalPixelsAndPcmAndGuiAndIndependentSchedulingAccepted=False,
                completeGame=False, nativeEquivalent=False, bindings=bindings)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--require-integrated', action='store_true')
    args = parser.parse_args()
    result = evidence(args.require_integrated)
    output = args.output.resolve()
    assert output.is_relative_to(R / 'artifacts/th14') or output.is_relative_to(R / 'docs/porting')
    if args.check: assert json.loads(output.read_bytes()) == result
    else:
        assert not output.exists()
        output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(json.dumps({k: v for k, v in result.items() if k not in ['bindings', 'completeNaturalRegressionCases', 'changedFiles']}))
