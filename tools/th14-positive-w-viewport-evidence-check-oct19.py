"""Recompute the TH14 positive-W viewport checkpoint from retained bytes."""
from pathlib import Path
import argparse, array, hashlib, json, math, struct

R = Path(__file__).resolve().parents[1]
A = R / 'artifacts/th14'
OUT = R / 'docs/porting/th14-positive-w-viewport-observed-oct19.json'
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
        a = array.array('I'); a.frombytes(b)
        return a

    base = A / 'primitive-viewport-bounded-v2-candidate-oct19'
    candidate = A / 'positive-w-viewport-candidate-oct19'
    source_before = A / 'primitive-viewport-bounded-sdl-v2-oct19/source'
    native = load(A / 'stage-gpu-stream-replay/native.json')
    pixels = read(A / 'stage-gpu-stream-replay/native.bgra')
    assert SHA(pixels) == native['pixelsSha256']
    cases = load(candidate / 'uv-cases.json')['cases']
    # Ten historical Native full buffers are retained; the other thirteen
    # historical cases have an independently captured full-buffer hash only.
    references = {}
    for folder, filename in [('world-uv', 'native.rgba32f'), ('sampler-uv-worst', 'full.rgba32f'), ('sampler-uv-strip', 'full.rgba32f')]:
        d = A / 'stage-gpu-stream-replay' / folder
        report = load(d / 'native.json'); raw = read(d / filename)
        for row in report['frames']:
            b = raw[row['offset']:row['offset'] + row['bytes']] if folder == 'world-uv' else raw
            assert SHA(b) == row.get('sha256', row.get('fullFloatFrameSha256'))
            references[row['stage'], row['frame'], row['originalDrawIndex']] = b
    groups = {}
    for mode in ['color', 'uv']:
        build = load(candidate / mode / 'build.json')
        assert SHA(read(candidate / mode / 'gpu.wasm')) == build['wasmSha256']
        assert SHA(read(candidate / mode / 'gpu.mjs')) == build['loaderSha256']
        for name, row in build['sources'].items():
            b = read(candidate / mode / name); assert len(b) == row['bytes'] and SHA(b) == row['sha256']
        for name, row in build['sourceBindings'].items():
            p = source_before / name.removeprefix('runtimes/th12/') if name.startswith('runtimes/th12/portable/sdl/') else R / name
            b = read(p); assert len(b) == row['bytes'] and SHA(b) == row['sha256']
        report = load(candidate / mode / 'capture/report.json')
        old = load(base / mode / 'capture/report.json')
        assert len(report['reports']) == (21 if mode == 'color' else 23)
        rows = []
        for row, prior in zip(report['reports'], old['reports']):
            actual = read(candidate / mode / 'capture' / row['savedFile'])
            previous = read(base / mode / 'capture' / prior['savedFile'])
            assert SHA(actual) == row['portableSha256'] and SHA(previous) == prior['portableSha256']
            assert not prior['strictFullBufferHashEqual'] or row['strictFullBufferHashEqual']
            rr = dict(stage=row['stage'], frame=row['frame'], nativeExact=SHA(actual) == row['nativeSha256'])
            if mode == 'color':
                n = native['frames'][row['index']]; expected = pixels[n['offset']:n['offset'] + n['bytes']]
                assert SHA(expected) == row['nativeSha256']
                rr.update(before=sum(x != y for x, y in zip(previous, expected)), after=sum(x != y for x, y in zip(actual, expected)))
                assert rr['after'] == row['differentChannels'] and rr['after'] <= rr['before']
            else:
                key = row['stage'], row['frame'], row['originalDrawIndex']; rr['draw'] = key[2]
                assert rr['nativeExact'] and row['nativeSha256'] == cases[row['index']]['nativeSha256']
                if key in references: assert actual == references[key]
            rows.append(rr)
        groups[mode] = rows
    assert sum(r['before'] for r in groups['color']) == 818
    assert sum(r['after'] for r in groups['color']) == 451

    held = A / 'positive-w-heldout-native-oct19'
    inputs = load(held / 'inputs.json'); n = load(held / 'native.json')
    assert n['toolSha256'] == inputs['toolSha256'] == SHA(read(held / 'capture-hal.py'))
    assert n['preparedSha256'] == inputs['preparedSha256'] == SHA(read(A / 'stage-gpu-stream-replay/prepared.json'))
    assert len(n['frames']) == len(inputs['cases']) == 24
    read(held / 'check.html'); read(held / 'serve.mjs')
    held_rows = []
    reports = {v: load(held / v / 'capture/report.json') for v in ['base', 'candidate']}
    for i, row in enumerate(n['frames']):
        c = inputs['cases'][i]; key = row['stage'], row['frame'], row['originalDrawIndex']
        assert key == (c['stage'], c['frame'], c['draw'])
        assert key not in {(x['stage'], x['frame'], x['originalDrawIndex']) for x in cases}
        expected = read(held / f'frame-{i:03}.rgba32f'); assert SHA(expected) == row['fullFloatFrameSha256']
        values = words(expected); empty = not any(values[k] for k in range(3, len(values), 4))
        rr = dict(stage=key[0], frame=key[1], draw=key[2], empty=empty)
        for v in ['base', 'candidate']:
            r = reports[v]['reports'][i]; b = read(held / v / 'capture' / r['savedFile'])
            assert SHA(b) == r['portableSha256'] and r['nativeSha256'] == SHA(expected)
            rr[v + 'Differences'] = sum(x != y for x, y in zip(words(b), values))
        assert rr['candidateDifferences'] == 0
        held_rows.append(rr)
    assert sum(r['baseDifferences'] == 0 for r in held_rows) == 22 and sum(r['empty'] for r in held_rows) == 4

    micro = A / 'viewport-positive-w-control-oct19'
    synthetic = words(read(A / 'viewport-boundary-valid-w-v2-oct19/native-run/b-full.rgba32f'))
    boundary = []
    for label in ['b', 'c', 'd']:
        raw = read(micro / f'capture/{label}-pixels.rgba32f'); tf = read(micro / f'capture/{label}-tf.f32')
        assert all(math.isfinite(x[0]) for x in struct.iter_unpack('<f', raw + tf))
        w = words(raw)
        boundary.append(dict(arm=label, words=sum(x != y for x, y in zip(w, synthetic)), coverage=sum((w[i] != 0) != (synthetic[i] != 0) for i in range(3, len(w), 4))))
    assert boundary == [dict(arm='b', words=194071, coverage=0), dict(arm='c', words=230520, coverage=2), dict(arm='d', words=194071, coverage=0)]
    assert read(micro / 'capture/b-pixels.rgba32f') == read(micro / 'capture/d-pixels.rgba32f')
    interval = A / 'positive-w-primitive-interval-oracle-oct19'
    check = load(interval / 'report.json'); all_cases = load(interval / 'all-cases.json')
    assert check['cases'] == len(all_cases) == 5012 and check['accepted'] == 1879 and not check['failures']
    assert SHA(read(interval / 'all-cases.json')) == check['allCasesSha256']
    assert SHA(read(interval / 'probe.wasm')) == check['wasmSha256']
    fixture = load(interval / 'source-binding.json'); s = read(R / fixture['path']).decode()
    helper = s[s.index('bool th14_primitive_projectable('):].split('\n#endif', 1)[0]
    assert SHA(helper.encode()) == fixture['helperSha256']
    for name in ['fixture.cpp', 'run.mjs', 'build.json']: read(interval / name)

    release_dir = A / 'positive-w-viewport-sdl-oct19'
    release = load(release_dir / 'build.json'); old = load(A / 'primitive-viewport-bounded-sdl-v2-oct19/build.json')
    changed = []
    for group in ['sourceHashes', 'headerHashes']:
        for name, digest in release[group].items():
            assert SHA(read(release_dir / 'source' / name)) == digest
            if old[group][name] != digest: changed.append(name); assert SHA(read(R / 'runtimes/th12' / name)) == digest
    assert changed == ['portable/sdl/Renderer.cpp']
    assert release['sourceFiles'] == len(release['objectHashes']) == 146 and release['importsUnchanged'] and release['exportsUnchanged']
    for name, digest in release['objectHashes'].items(): assert SHA(read(release_dir / name)) == digest
    assert SHA(read(release_dir / 'th11.wasm')) == release['wasmSha256'] == 'a8b3ff4a6ca9f8138562798bd89db3a9a84bee2a7f1d5291019e6256a2b2a2e0'
    assert SHA(read(release_dir / 'th11.mjs')) == release['loaderSha256']
    assert release['sourceHashes']['th12_web/cpp/game/ResourceCrypt.cpp'] == 'd57118f1114f3909c42a2e99e7df30e625f6563247a8118cd14bb9f68a0f97ef'
    runtime = load(R / 'docs/porting/th14-launcher-runtime-positive-w-viewport-oct19.json')
    site = load(R / 'docs/porting/th14-launcher-site-positive-w-viewport-oct19.json')
    for report, folder in [(runtime, runtime['out']), (site, site['site'])]:
        for name, row in report['files'].items():
            b = read(Path(folder) / name); assert len(b) == row['bytes'] and SHA(b) == row['sha256']
    browser = load(A / 'positive-w-viewport-preview-oct19/observed.json')
    assert browser['oldReplayFilesVisible'] == 4 and browser['quietMarkerVisible'] and not browser['warningsAndErrors']
    assert browser['ordinaryReplayMenuUsed'] and browser['selectedStage'] == 2 and not browser['naturalReplayEofObserved']
    read(A / 'positive-w-viewport-preview-oct19/four-replays-retained.jpg')
    read(A / 'positive-w-viewport-preview-oct19/stage2-running.jpg')
    read(A / 'positive-w-viewport-adoption-oct19/receipt.json'); read(Path(__file__))
    return dict(evidenceVerified=True, changed=changed, sourceGameplayChanged=False, colorDifferences=451, baselineColorDifferences=818, exactHistoricalUv=23, historicalUvCases=23, historicalNativeFullBytesCases=10, heldoutCases=24, heldoutExact=24, heldoutBaselineExact=22, heldoutEmptyCases=4, comparisons=groups, heldoutComparisons=held_rows, boundary=boundary, intervalCases=5012, intervalAccepted=1879, intervalVariants=3741696, sdlCompiledSources=146, wasmSha256=release['wasmSha256'], browserOldReplays=4, browserStage=2, completeGame=False, nativeEquivalent=False, scope='Declared positive-W/depth whole-primitive compatibility and retained recorded outputs. Side-plane clipping allowed uniformly. Historical thirteen UV references are full-frame hashes only. Four empty held-out cases retained. Interval FMA enumeration uses double intermediate approximations. Remaining color, visual RNG, shot lifetime, audio, original ordinary menu and whole-game/cross-hardware equivalence not certified. Historical checks retain their original source bindings.', bindings=bindings)


def main():
    p = argparse.ArgumentParser(); p.add_argument('--write', action='store_true'); p.add_argument('--check', action='store_true'); args = p.parse_args()
    assert args.write != args.check; result = inspect()
    if args.write:
        with OUT.open('x', encoding='utf-8') as f: json.dump(result, f, indent=2); f.write('\n')
    else: assert json.loads(OUT.read_bytes()) == result
    print(json.dumps(dict(evidenceVerified=True, colorDifferences=451, historicalUv=23, heldoutUv=24, bindings=len(result['bindings']), completeGame=False, nativeEquivalent=False)))


if __name__ == '__main__': main()
