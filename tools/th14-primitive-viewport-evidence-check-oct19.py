"""Recompute the bounded TH14 viewport checkpoint without starting a device."""
from pathlib import Path
import argparse, array, hashlib, json, math, struct

R = Path(__file__).resolve().parents[1]
A = R / 'artifacts/th14'
OUT = R / 'docs/porting/th14-primitive-viewport-observed-oct19.json'
SHA = lambda b: hashlib.sha256(b).hexdigest()


def inspect():
    bindings = {}

    def read(p):
        b = p.read_bytes()
        bindings[p.relative_to(R).as_posix()] = dict(bytes=len(b), sha256=SHA(b))
        return b

    def load(p):
        return json.loads(read(p))

    def words(b):
        result = array.array('I'); result.frombytes(b)
        return result

    base = A / 'stage-production-clip-no-finite-guard-oct14'
    candidate = A / 'primitive-viewport-bounded-v2-candidate-oct19'
    frozen = A / 'dialogue-damage-sdl-build-oct18/source'
    native = load(A / 'stage-gpu-stream-replay/native.json')
    native_bytes = read(A / 'stage-gpu-stream-replay/native.bgra')
    assert SHA(native_bytes) == native['pixelsSha256']
    references = {}
    for folder, filename in [('world-uv', 'native.rgba32f'), ('sampler-uv-worst', 'full.rgba32f'), ('sampler-uv-strip', 'full.rgba32f')]:
        d = A / 'stage-gpu-stream-replay' / folder
        report = load(d / 'native.json'); raw = read(d / filename)
        for row in report['frames']:
            b = raw[row['offset']:row['offset'] + row['bytes']] if folder == 'world-uv' else raw
            assert SHA(b) == row.get('sha256', row.get('fullFloatFrameSha256'))
            references[row['stage'], row['frame'], row['originalDrawIndex']] = b
    for folder in ['stage-current-residual-native-uv-fe406-oct14', 'viewport-regression-native-oct19']:
        d = A / folder
        for i, row in enumerate(load(d / 'native.json')['frames']):
            b = read(d / f'frame-{i:03}.rgba32f'); assert SHA(b) == row['fullFloatFrameSha256']
            references[row['stage'], row['frame'], row['originalDrawIndex']] = b

    rows = []
    for mode in ['color', 'uv']:
        build = load(candidate / mode / 'build.json')
        assert SHA(read(candidate / mode / 'gpu.wasm')) == build['wasmSha256']
        assert SHA(read(candidate / mode / 'gpu.mjs')) == build['loaderSha256']
        for name, row in build['sources'].items():
            b = read(candidate / mode / name); assert len(b) == row['bytes'] and SHA(b) == row['sha256']
        for name, row in build['sourceBindings'].items():
            p = frozen / name.removeprefix('runtimes/th12/') if name.startswith('runtimes/th12/portable/sdl/') else R / name
            b = read(p); assert len(b) == row['bytes'] and SHA(b) == row['sha256']
        report = load(candidate / mode / 'capture/report.json')
        old = load(base / mode / 'capture/report.json')
        assert len(report['reports']) == (21 if mode == 'color' else 23)
        mode_rows = []
        for row, prior in zip(report['reports'], old['reports']):
            actual = read(candidate / mode / 'capture' / row['savedFile'])
            previous = read(base / mode / 'capture' / prior['savedFile'])
            assert SHA(actual) == row['portableSha256'] and SHA(previous) == prior['portableSha256']
            assert not prior['strictFullBufferHashEqual'] or row['strictFullBufferHashEqual']
            rr = dict(stage=row['stage'], frame=row['frame'], nativeExact=SHA(actual) == row['nativeSha256'])
            assert rr['nativeExact'] == row['strictFullBufferHashEqual']
            if mode == 'color':
                n = native['frames'][row['index']]
                expected = native_bytes[n['offset']:n['offset'] + n['bytes']]
                assert SHA(expected) == row['nativeSha256']
                rr.update(baselineDifferences=sum(x != y for x, y in zip(previous, expected)), differences=sum(x != y for x, y in zip(actual, expected)))
                assert rr['differences'] == row['differentChannels'] and rr['differences'] <= rr['baselineDifferences']
            else:
                key = row['stage'], row['frame'], row['originalDrawIndex']; rr['draw'] = key[2]
                if key in references:
                    expected = references[key]; assert SHA(expected) == row['nativeSha256']
                    x, y = words(actual), words(expected)
                    rr.update(comparedNativeWords=len(y), differences=sum(a != b for a, b in zip(x, y)), coverageDifferences=sum((x[i] != 0) != (y[i] != 0) for i in range(3, len(y), 4)))
                    assert rr['coverageDifferences'] == 0
            mode_rows.append(rr)
        rows.append(dict(mode=mode, exactBuffers=sum(r['nativeExact'] for r in mode_rows), rows=mode_rows))
    assert rows[0]['exactBuffers'] == 3 and sum(r['differences'] for r in rows[0]['rows']) == 818
    assert sum(r['baselineDifferences'] for r in rows[0]['rows']) == 880 and rows[1]['exactBuffers'] == 22

    micro = A / 'viewport-primitive-guard-oct19'
    report = load(micro / 'capture/report.json'); assert report['executionCompleted'] and report['drawCalls'] == 4
    synthetic = words(read(A / 'viewport-boundary-valid-w-v2-oct19/native-run/b-full.rgba32f'))
    boundary_rows = []
    for label in ['b', 'c', 'd']:
        raw = read(micro / f'capture/{label}-pixels.rgba32f'); tf = read(micro / f'capture/{label}-tf.f32')
        assert all(math.isfinite(x[0]) for x in struct.iter_unpack('<f', tf))
        assert all(math.isfinite(x[0]) for x in struct.iter_unpack('<f', raw))
        pw = words(raw)
        boundary_rows.append(dict(arm=label, differences=sum(x != y for x, y in zip(pw, synthetic)), coverageDifferences=sum((pw[i] != 0) != (synthetic[i] != 0) for i in range(3, len(pw), 4))))
    assert boundary_rows == [dict(arm='b', differences=194071, coverageDifferences=0), dict(arm='c', differences=230520, coverageDifferences=2), dict(arm='d', differences=194071, coverageDifferences=0)]
    assert read(micro / 'capture/b-pixels.rgba32f') == read(micro / 'capture/d-pixels.rgba32f')

    interval = A / 'bounded-primitive-interval-oracle-oct19'
    check = load(interval / 'report.json'); cases = load(interval / 'all-cases.json')
    assert check['cases'] == len(cases) == 5011 and check['accepted'] == 1516 and not check['failures']
    assert SHA(read(interval / 'all-cases.json')) == check['allCasesSha256']
    assert SHA(read(interval / 'probe.wasm')) == check['wasmSha256']
    fixture_binding = load(interval / 'source-binding.json')
    s = read(R / fixture_binding['path']).decode(); helper = s[s.index('bool th14_primitive_inside('):]; helper = helper.split('\n#endif', 1)[0]
    assert SHA(helper.encode()) == fixture_binding['helperSha256']
    read(interval / 'fixture.cpp'); read(interval / 'run.mjs'); read(interval / 'build.json')

    release_dir = A / 'primitive-viewport-bounded-sdl-v2-oct19'
    release = load(release_dir / 'build.json'); old = load(A / 'dialogue-damage-sdl-build-oct18/build.json')
    changed = []
    for group in ['sourceHashes', 'headerHashes']:
        for name, digest in release[group].items():
            assert SHA(read(release_dir / 'source' / name)) == digest
            if old[group][name] != digest:
                changed.append(name); assert SHA(read(R / 'runtimes/th12' / name)) == digest
    assert changed == ['portable/sdl/Renderer.cpp', 'portable/sdl/Shaders.hpp']
    assert release['sourceFiles'] == len(release['objectHashes']) == 146 and release['exportsUnchanged']
    for name, digest in release['objectHashes'].items(): assert SHA(read(release_dir / name)) == digest
    assert SHA(read(release_dir / 'th11.wasm')) == release['wasmSha256'] == '9e01f35d99a13325543c6329a02cdbdd73919bd6a66ec66846bef3a8d3d556d8'
    assert SHA(read(release_dir / 'th11.mjs')) == release['loaderSha256']
    browser = load(A / 'primitive-viewport-preview-oct19/stage2-observed.json')
    assert browser['oldReplayFilesVisible'] == 4 and browser['quietMarkerVisible'] and not browser['warningsAndErrors']
    assert browser['selectedStage'] == 2 and browser['ordinaryReplayMenuUsed'] and not browser['naturalReplayEofObserved']
    read(A / 'primitive-viewport-preview-oct19/reimub-stage2-running.jpg')
    read(A / 'primitive-viewport-preview-oct19/four-replays-retained.jpg')
    read(A / 'primitive-viewport-adoption-oct19/receipt.json')
    read(A / 'primitive-viewport-shared-renderer-check-oct19/report.json')
    read(Path(__file__))
    return dict(evidenceVerified=True,adoptedGraphicsFiles=changed,sourceGameplayChanged=False,colorDifferences=818,baselineColorDifferences=880,exactUvBuffers=22,totalUvBuffers=23,oldPassingRegressions=0,frameComparisons=rows,boundaryControls=boundary_rows,intervalCases=5011,intervalAccepted=1516,intervalRejected=3495,roundingVariantsChecked=3014208,sdlCompiledSources=146,wasmSha256=release['wasmSha256'],importsUnchanged=release['importsUnchanged'],exportsUnchanged=True,browserOldReplayFiles=4,browserStageObserved=2,browserNaturalEofObserved=False,completeGame=False,nativeEquivalent=False,scope='Bounded whole-primitive compatibility change. Recorded color/UV and declared boundary evidence only; remaining clipping, interpolation, visual RNG, audio, arbitrary hardware and complete ordinary-original workflow are not certified. Earlier rejected candidates remain rejected. Historical checks tied to old Root graphics bytes are not current-source checks.',bindings=bindings)


def main():
    p = argparse.ArgumentParser(); p.add_argument('--write', action='store_true'); p.add_argument('--check', action='store_true'); args = p.parse_args()
    assert args.write != args.check; result = inspect()
    if args.write:
        with OUT.open('x', encoding='utf-8') as f: json.dump(result, f, indent=2); f.write('\n')
    else:
        assert json.loads(OUT.read_bytes()) == result
    print(json.dumps(dict(evidenceVerified=True,colorDifferences=818,exactUvBuffers=22,bindings=len(result['bindings']),completeGame=False,nativeEquivalent=False)))


if __name__ == '__main__': main()
