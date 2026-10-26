"""Independently verify retained whole-buffer native viewport controls.

This reads private component evidence. It does not run or control a browser,
modify production graphics, or assert that the native intervention is WebGL.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda raw: hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/porting/th14-native-gles-viewport-verified-oct26.json')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    bindings = {}

    def read(path):
        raw = path.read_bytes()
        bindings[path.relative_to(ROOT).as_posix()] = dict(bytes=len(raw), sha256=SHA(raw))
        return raw

    def load(path):
        return json.loads(read(path))

    baseline_home = ROOT / 'artifacts/th14/native-gles-production-tool-oct26/replay'
    probe_home = ROOT / 'artifacts/th14/native-gles-postclip-viewport-bound-oct26'
    build_home = ROOT / 'artifacts/th14/native-gles-production-tool-oct26/build'
    build = load(build_home / 'build.json')
    assert SHA(read(build_home / 'probe.wasm')) == build['wasmSha256']
    for path, row in build['sourceBindings'].items():
        raw = read(ROOT / path)
        assert len(raw) == row['bytes'] and SHA(raw) == row['sha256']
    reference_home = ROOT / 'artifacts/th14/stage-gpu-stream-replay'
    native = load(reference_home / 'native.json')
    reference = read(reference_home / 'native.bgra')
    assert SHA(reference) == native['pixelsSha256']
    prepared_sha = SHA(read(reference_home / 'prepared.json'))
    baseline, probe = load(baseline_home / 'comparison.json'), load(probe_home / 'comparison.json')
    assert baseline['retainedBrowserBaseline']['allFullBuffersReproduced']
    assert baseline['retainedBrowserBaseline']['allShaderSourcesIdentical']
    assert probe['nativeD3D11ViewportIntervention'] and probe['viewportCalls'] > 0 and probe['viewportInterventions'] > 0
    assert probe['clipControlEnabled'] and baseline['clipControlEnabled']
    assert not baseline['browserRun'] and not probe['browserRun'] and not probe['productionChanged']
    assert SHA(read(probe_home / 'run.py')) == probe['toolSha256']
    assert SHA(read(ROOT / 'artifacts/th14/run-native-gles-variant-oct26.py')) == probe['derivationSha256']
    assert SHA(read(ROOT / 'artifacts/th14/native-gles-viewport-controller-oct26.py')) == probe['viewportControllerSha256']
    results = []
    for home, report in [(baseline_home, baseline), (probe_home, probe)]:
        assert report['wasmSha256'] == build['wasmSha256']
        assert report['nativePixelsSha256'] == SHA(reference) and report['preparedSha256'] == prepared_sha
        assert len(report['rows']) == report['frames'] == len(native['frames']) == 21
        rows, whole = [], hashlib.sha256()
        for row, target in zip(report['rows'], native['frames']):
            assert (row['stage'], row['frame']) == (target['stage'], target['frame'])
            raw = read(home / f"stage{row['stage']}-frame{row['frame']}.bgra")
            expected = reference[target['offset']:target['offset'] + target['bytes']]
            assert len(raw) == len(expected) == 640 * 480 * 4
            assert SHA(raw) == row['actualSha256'] and SHA(expected) == row['originalSha256'] == target['sha256']
            differences = sum(left != right for left, right in zip(raw, expected))
            assert differences == row['differentChannels']
            whole.update(raw)
            rows.append(dict(stage=row['stage'], frame=row['frame'], differentChannels=differences, actualSha256=SHA(raw), originalSha256=SHA(expected)))
        assert whole.hexdigest() == report['actualPixelsSha256']
        result = dict(exactFrames=sum(not row['differentChannels'] for row in rows), differentChannels=sum(row['differentChannels'] for row in rows), rows=rows)
        assert result['exactFrames'] == report['exactFrames'] and result['differentChannels'] == report['differentChannels']
        results.append(result)
    assert (results[0]['exactFrames'], results[0]['differentChannels']) == (20, 1)
    assert (results[1]['exactFrames'], results[1]['differentChannels']) == (21, 0)
    before = load(baseline_home / 'shader-sources.json')
    after = load(probe_home / 'shader-sources.json')
    assert len(before) == len(after) == 38
    assert [SHA(source.encode()) for source in before] == baseline['shaderHashes']
    assert [SHA(source.encode()) for source in after] == probe['shaderHashes']
    changed = [index for index, pair in enumerate(zip(before, after)) if pair[0] != pair[1]]
    assert changed == [2]
    vertex = before[2]
    numerator = 'vec2 numerator=gl_Position.xy*viewport.zw+vec2(gl_Position.w);gl_Position.xy=numerator/viewport.zw;'
    eligible = '((pixel+vec2(0.5))/halfViewport-vec2(1.0))*original.w'
    assert vertex.count(numerator) == vertex.count(eligible) == 1
    assert vertex.replace(numerator, '').replace(eligible, '(pixel/halfViewport-vec2(1.0))*original.w') == after[2]
    result = dict(verifiedFiniteEvidence=True, frames=21, referenceBytes=len(reference), baseline=results[0], postclipNativeViewport=results[1], onlyOneSubmittedVertexShaderChanged=True, fragmentShaderSourcesUnchanged=True, halfPixelAppliedByNativeD3D11AfterClipping=True, viewportInterventions=probe['viewportInterventions'], wasmSha256=build['wasmSha256'], productionChanged=False, productionWebglFix=False, currentBrowserAcceptance=False, audioDevicesOpened=0, completeGame=False, nativeEquivalent=False, verifierSha256=SHA(Path(__file__).read_bytes()), bindings=bindings, limitations=['Same finite Stage command streams, declared initial state and controlled screen-queue exclusions as the retained component.', 'A private standalone ANGLE context permits a native D3D11 viewport intervention; this is not available through the production WebGL viewport API.', 'No actual original complete framebuffer, ordinary gameplay, complete renderer or current browser acceptance is proved.'])
    output = args.output.resolve()
    assert output.is_relative_to(ROOT / 'docs/porting') or output.is_relative_to(ROOT / 'artifacts/th14')
    if args.check:
        assert json.loads(output.read_bytes()) == result
    else:
        output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(verifiedFiniteEvidence=True, baselineExact=20, postclipNativeExact=21, productionWebglFix=False)))


if __name__ == '__main__':
    main()
