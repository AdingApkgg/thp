"""Recompute the finite actual-C++ WebGPU evidence; never infer whole-game parity."""
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
    args = parser.parse_args(); home = args.home.resolve(strict=True); bindings = {}
    assert home.is_relative_to(ROOT/'artifacts/th14')
    def read(path):
        raw = path.read_bytes(); bindings[path.relative_to(ROOT).as_posix()] = dict(bytes=len(raw), sha256=SHA(raw)); return raw
    def load(path): return json.loads(read(path))
    def source_bindings(build):
        for path, row in build['sourceBindings'].items():
            raw = read(ROOT/path); assert len(raw) == row['bytes'] and SHA(raw) == row['sha256'], path
    def component_build(folder):
        build = load(folder/'build.json'); source_bindings(build)
        assert build['wasmSha256'] == SHA(read(folder/'probe.wasm'))
        assert build['toolSha256'] == SHA(read(ROOT/'tools/th14-build-native-gles-component.py'))
        for name, digest in build['sourceFiles'].items(): assert SHA(read(folder/'src'/name)) == digest
        for name, digest in build['shimFiles'].items(): assert SHA(read(folder/'include'/name)) == digest
        return build
    stage_build = component_build(home/'stage-build-final')
    surface_build = component_build(home/'surface-build-v2')
    assert stage_build['backend'] == surface_build['backend'] == 'webgpu'
    stage = load(home/'stage-final/comparison.json')
    assert stage['actualProductionCppRenderer'] and not stage['backendHostFfpMath']
    assert stage['wasmSha256'] == stage_build['wasmSha256']
    assert stage['buildSha256'] == SHA(read(home/'stage-build-final/build.json'))
    assert stage['toolSha256'] == SHA(read(ROOT/'tools/th14-native-webgpu-component.py'))
    assert stage['contextToolSha256'] == SHA(read(ROOT/'tools/th14-native-webgpu-context.py'))
    reference = ROOT/'artifacts/th14/stage-gpu-stream-replay'
    native = load(reference/'native.json'); raw = read(reference/'native.bgra')
    assert stage['preparedSha256'] == SHA(read(reference/'prepared.json'))
    assert stage['nativeReportSha256'] == SHA(read(reference/'native.json'))
    assert SHA(raw) == stage['nativePixelsSha256'] == native['pixelsSha256']
    stage_rows, total = [], 0
    assert len(stage['rows']) == len(native['frames']) == 21
    for row in stage['rows']:
        n = next(v for v in native['frames'] if (v['stage'], v['frame']) == (row['stage'], row['frame']))
        actual = read(home/f"stage-final/stage{row['stage']}-frame{row['frame']}.bgra")
        expected = raw[n['offset']:n['offset']+n['bytes']]
        assert len(actual) == len(expected) == 640*480*4 and actual == expected
        assert SHA(actual) == row['actualSha256'] == row['originalSha256'] == n['sha256'] and row['differentChannels'] == 0
        total += len(actual); stage_rows.append(dict(stage=row['stage'], frame=row['frame'], sha256=SHA(actual)))
    assert stage['exactFrames'] == 21 and stage['differentChannels'] == 0
    surfaces = load(home/'surfaces-final/report.json')
    assert surfaces['wasmSha256'] == surface_build['wasmSha256'] and surfaces['cases'] == surfaces['exactCases'] == 8
    assert surfaces['buildSha256'] == SHA(read(home/'surface-build-v2/build.json'))
    assert surfaces['toolSha256'] == SHA(read(ROOT/'tools/th14-native-webgpu-surfaces.py'))
    assert surfaces['hostToolSha256'] == SHA(read(ROOT/'tools/th14-native-webgpu-context.py'))
    surface_reference = ROOT/'artifacts/th14/deferred-capture-pixels-oct14'
    original_surfaces = load(surface_reference/'native.json')
    assert surfaces['nativeReportSha256'] == SHA(read(surface_reference/'native.json'))
    assert surfaces['inputsSha256'] == SHA(read(surface_reference/'inputs.json'))
    assert surfaces['sourceSha256'] == SHA(read(surface_reference/'source.bgra'))
    surface_total = 0
    for row, n in zip(surfaces['rows'], original_surfaces['cases']):
        actual = read(home/f"surfaces-final/case-{row['index']}.pixels"); expected = read(surface_reference/n['pixelFile'])
        assert actual == expected and SHA(actual) == row['actualSha256'] == row['nativeSha256'] == n['pixelSha256']
        assert row['differentBytes'] == 0; surface_total += len(actual)
    assert surface_total == surfaces['comparedBytes'] and surfaces['rectangleControls']['exact']
    width, height = 96, 128
    prefill = bytes.fromhex('a1b2c3d4')*(width*height); expected = bytearray(prefill)
    for left, top, right, bottom in [(3, 7, 49, 61), (47, 43, 90, 119)]:
        for y in range(top, bottom): expected[(y*width+left)*4:(y*width+right)*4] = (0xffa15127).to_bytes(4, 'little')*(right-left)
    assert read(home/'surfaces-final/partial-clear.bgra') == expected
    expected[(8*width+4)*4:(8*width+5)*4] = bytes.fromhex('225577ff')
    copied = bytearray(prefill)
    for y in range(43): copied[((19+y)*width+17)*4:((19+y)*width+52)*4] = expected[((8+y)*width+4)*4:((8+y)*width+39)*4]
    assert read(home/'surfaces-final/version-copy.bgra') == copied
    application_builds = {}
    for name in ['application-build-final', 'application-build-gles-control']:
        build = load(home/name/'build.json'); source_bindings(build)
        assert build['compiled'] and build['wasmSha256'] == SHA(read(home/name/'application.wasm'))
        assert build['toolSha256'] == SHA(read(home/name/'build-tool.py')) == SHA(read(ROOT/'tools/th14-build-native-application.py'))
        assert len(build['coreObjects']) == 141
        for row in build['coreObjects']: assert SHA(read(Path(row['path']))) == row['sha256']
        application_builds[build['backend']] = (name, build)
    checks_total, capture_total, frames_total = 0, 0, 0
    app_rows = []
    for directory, scenario_name, frames, checks in [('workflow', 'save-replay', 1286, 218), ('reload', 'reload-replay', 722, 21)]:
        runs = {}
        scenario_path = ROOT/f'runtimes/th12/th12_web/tests/fixtures/th14-native-application-{scenario_name}.json'
        scenario = load(scenario_path)
        for backend, suffix in [('webgpu', 'final'), ('gles', 'gles-control')]:
            folder = home/f'{directory}-{suffix}'; run = load(folder/'report.json'); build_name, build = application_builds[backend]
            assert run['backend'] == backend and run['completed'] and not run['error']
            assert run['metadataEpochAtFrameZero'] == 1792965600 and run['scenarioSha256'] == SHA(read(scenario_path))
            assert run['wasmSha256'] == build['wasmSha256'] and run['buildReportSha256'] == SHA(read(home/build_name/'build.json'))
            assert run['toolSha256'] == SHA(read(folder/'run-tool.py')) == SHA(read(ROOT/'tools/th14-native-application.py'))
            assert run['hostToolSha256'] == SHA(read(ROOT/('tools/th14-native-webgpu-context.py' if backend == 'webgpu' else 'tools/th14-native-gles-context.py')))
            assert run['frames'] == frames and len(run['checks']) == checks
            assert run['physicalAudioDevicesOpened'] == 0 and run['virtualAudioStreamsCreated'] == 1
            assert not any(run[k] for k in ['appUiControlled', 'browserRun', 'browserAcceptance', 'completeGame', 'nativeEquivalent'])
            journal, at = [], 0
            for command, action in zip(scenario['actions'], run['actions']):
                assert action['atFrame'] == at
                for field in ['frames', 'held', 'pause']: assert action[field] == command.get(field, 0)
                at += command.get('frames', 0); assert action['endFrame'] == at
                for index, value in command.get('expect', {}).items():
                    actual = action['state'][int(index)]; assert actual == value
                    journal.append(dict(frame=at, index=int(index), expected=value, actual=actual, passed=True))
            assert at == frames and len(run['actions']) == len(scenario['actions']) and journal == run['checks']
            for row in run['captures']: assert SHA(read(folder/row['file'])) == row['sha256']
            for path, row in run['finalSave'].items():
                saved = read(folder/'save'/path); assert len(saved) == row['bytes'] and SHA(saved) == row['sha256']
            if backend == 'webgpu': assert not any(k.startswith('gl') for k in run['glCalls'])
            runs[backend] = run
        a, b = runs['webgpu'], runs['gles']
        assert a['actions'] == b['actions'] and a['checks'] == b['checks'] and a['finalSave'] == b['finalSave']
        assert a['pcmFrames'] == b['pcmFrames'] and a['pcmSha256'] == b['pcmSha256']
        assert len(a['captures']) == len(b['captures'])
        for x, y in zip(a['captures'], b['captures']):
            assert x['label'] == y['label'] and x['sha256'] == y['sha256']
            assert read(home/f'{directory}-final'/x['file']) == read(home/f'{directory}-gles-control'/y['file'])
        checks_total += len(a['checks']); capture_total += len(a['captures']); frames_total += a['frames']
        app_rows.append(dict(scenario=directory, frames=frames, assertions=checks, exactPairedCaptures=len(a['captures']), pcmSha256=a['pcmSha256'], files=a['finalSave']))
    workflow = load(home/'workflow-final/report.json'); reload = load(home/'reload-final/report.json')
    assert workflow['finalSave'] == reload['initialSave'] == reload['finalSave']
    codec = load(home/'native-files-final/report.json')
    assert codec['verifiedFiniteNativeCodecEvidence'] and codec['score']['originalFullLoaderBytesEqual'] and codec['score']['originalFullWriterBytesEqual']
    assert codec['toolSha256'] == SHA(read(ROOT/'tools/th14-native-application-files.py'))
    assert codec['replay']['sha256'] == workflow['finalSave']['replay/th14_01.rpy']['sha256']
    assert codec['score']['sha256'] == workflow['finalSave']['scoreth14.dat']['sha256']
    for name, key in [('replay', 'replay'), ('score', 'score')]: assert SHA(read(home/f'native-files-final/{name}-decoded.bin')) == codec[key]['decodedSha256']
    result = dict(schema='th14/cpp-webgpu-verified/1', independentlyRecomputedFiniteEvidence=True,
        actualProductionCppRenderer=True, optionalCppWebgpuBackendImplemented=True, defaultBackend='GLES/WebGL',
        defaultWebglFailureRetained=True, productionBrowserWebgpuHostImplemented=False, browserAcceptance=False,
        nativeStageFrames=21, nativeStageComparedBytes=total, nativeStageDifferentBytes=0, stageRows=stage_rows,
        nativeD3dxCaptureCases=8, nativeD3dxCaptureComparedBytes=surface_total, nativeD3dxCaptureDifferentBytes=0,
        surfaceRectangleControls=surfaces['rectangleControls'], applicationFrames=frames_total,
        applicationAssertions=checks_total, exactPairedApplicationCaptures=capture_total, applicationRuns=app_rows,
        metadataEpochAtFrameZero=1792965600, originalFileCodecsPassed=True, freshProcessFilesUnchanged=True,
        gpuOptionalFeatures=[], physicalAudioDevicesOpened=0, sourceBindings=stage_build['sourceBindings'], bindings=bindings,
        checkerSha256=SHA(Path(__file__).read_bytes()), completeGame=False, nativeEquivalent=False,
        remaining=['Browser WebGPU host, asynchronous initialization/readback and presentation are not implemented or accepted.',
                   'Packed render-target raster blending and partial stencil clears are rejected, not approximated.',
                   'Weighted resample shader and other pipeline/format paths require separate original controls.',
                   'Finite Stage references retain controlled screen-queue exclusions; Application captures compare backends, not original ordinary UI.',
                   'Full mode, camera interleaving, effect149 ABI/address, ordinary original UI, input/audio and browser persistence gaps remain.'])
    output = args.output.resolve(); assert output.is_relative_to(ROOT)
    if args.check: assert json.loads(output.read_bytes()) == result
    else:
        assert not output.exists(); output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k: result[k] for k in ['nativeStageFrames', 'nativeD3dxCaptureCases', 'applicationAssertions', 'exactPairedApplicationCaptures', 'completeGame']}))


if __name__ == '__main__':
    main()
