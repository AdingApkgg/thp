"""Recompute TH14-only depth conversion and retained GPU controls."""
from pathlib import Path
import argparse, hashlib, json

R = Path(__file__).resolve().parents[1]
A = R / 'artifacts/th14'
OUT = R / 'docs/porting/th14-fixed20-depth-observed-oct19.json'
SHA = lambda b: hashlib.sha256(b).hexdigest()


def inspect():
    bindings = {}

    def read(p):
        b = p.read_bytes(); bindings[p.relative_to(R).as_posix()] = dict(bytes=len(b), sha256=SHA(b)); return b

    def load(p): return json.loads(read(p))

    candidate = A / 'positive-w-fixed20-depth-v2-oct19'
    old = A / 'positive-w-viewport-candidate-oct19'
    frozen = A / 'positive-w-viewport-sdl-oct19/source'
    for mode in ['color', 'uv', 'alpha', 'depth']:
        d = candidate / mode; build = load(d / 'build.json')
        assert SHA(read(d / 'gpu.wasm')) == build['wasmSha256'] and SHA(read(d / 'gpu.mjs')) == build['loaderSha256']
        for name, row in build['sources'].items():
            b = read(d / name); assert len(b) == row['bytes'] and SHA(b) == row['sha256']
        for name, row in build['sourceBindings'].items():
            p = frozen / name.removeprefix('runtimes/th12/') if name.startswith('runtimes/th12/portable/sdl/') else R / name
            b = read(p); assert len(b) == row['bytes'] and SHA(b) == row['sha256']
        assert read(d / 'Renderer.cpp') == read(candidate / 'color/Renderer.cpp')
    # The only production change is the guarded source substitution. The
    # shared shader header remains byte-identical to the published snapshot.
    renderer = read(candidate / 'color/Renderer.cpp'); root_renderer = read(R / 'runtimes/th12/portable/sdl/Renderer.cpp')
    assert renderer == root_renderer
    assert read(candidate / 'color/Shaders.hpp') == read(R / 'runtimes/th12/portable/sdl/Shaders.hpp') == read(frozen / 'portable/sdl/Shaders.hpp')
    text = renderer.decode(); start = text.index('#if defined(PORT_TITLE) && PORT_TITLE == 14\n  // Installed D3D9 D16 conversion:')
    end = text.index('#endif\n', start) + len('#endif\n')
    assert (text[:start] + text[end:]).encode() == read(frozen / 'portable/sdl/Renderer.cpp')

    native = load(A / 'stage-gpu-stream-replay/native.json'); native_bytes = read(A / 'stage-gpu-stream-replay/native.bgra')
    assert SHA(native_bytes) == native['pixelsSha256']
    current = load(candidate / 'color/capture/report.json'); previous = load(old / 'color/capture/report.json')
    colors = []
    assert len(current['reports']) == len(previous['reports']) == 21
    for n, p, c in zip(native['frames'], previous['reports'], current['reports']):
        expected = native_bytes[n['offset']:n['offset'] + n['bytes']]
        before = read(old / 'color/capture' / p['savedFile']); after = read(candidate / 'color/capture' / c['savedFile'])
        assert SHA(expected) == c['nativeSha256'] and SHA(before) == p['portableSha256'] and SHA(after) == c['portableSha256']
        diff = sum(x != y for x, y in zip(after, expected)); prior = sum(x != y for x, y in zip(before, expected))
        assert diff == c['differentChannels'] and diff <= prior
        assert max(abs(x - y) for x, y in zip(after, expected)) <= 1
        colors.append(dict(stage=n['stage'], frame=n['frame'], before=prior, after=diff))
    assert sum(x['before'] for x in colors) == 451 and sum(x['after'] for x in colors) == 55
    cases = load(candidate / 'uv-cases.json'); uv = load(candidate / 'uv/capture/report.json')
    assert len(cases['cases']) == len(uv['reports']) == uv['exactFullBuffers'] == 47
    references = {}
    for row in cases['fullBindings']:
        p = Path(row['path']); p = p if p.is_absolute() else R / p
        raw = read(p); offset = row.get('offset', 0); b = raw[offset:offset + row['bytes']]
        assert SHA(b) == row['sha256']; references[row['key']] = b
    # Six additional historical full buffers were archived separately from
    # the browser server's four original full-buffer routes.
    for folder in ['stage-current-residual-native-uv-fe406-oct14', 'viewport-regression-native-oct19']:
        d = A / folder
        for i, row in enumerate(load(d / 'native.json')['frames']):
            b = read(d / f'frame-{i:03}.rgba32f'); assert SHA(b) == row['fullFloatFrameSha256']
            references['/'.join(str(row[k]) for k in ['stage', 'frame', 'originalDrawIndex'])] = b
    full_bytes = 0
    for n, c in zip(cases['cases'], uv['reports']):
        b = read(candidate / 'uv/capture' / c['savedFile'])
        assert SHA(b) == c['portableSha256'] == c['nativeSha256'] == n['nativeSha256']
        key = '/'.join(str(n[k]) for k in ['stage', 'frame', 'originalDrawIndex'])
        if key in references: assert b == references[key]; full_bytes += 1
    assert full_bytes == 34

    alpha = load(candidate / 'alpha/browser-report.json')
    alpha_native = load(A / 'gpu-alpha-depth/native.json'); pixels = read(A / 'gpu-alpha-depth/native.bgra')
    assert alpha['cases'] == alpha['exactCases'] == len(alpha_native['cases']) == 2560
    assert alpha['differentChannels'] == 0 and alpha['portablePixelsSha256'] == alpha['nativePixelsSha256'] == SHA(pixels) == alpha_native['pixelsSha256']
    assert alpha['wasmSha256'] == load(candidate / 'alpha/build.json')['wasmSha256']
    for i, c in enumerate(alpha_native['cases']): assert SHA(pixels[i * 4096:(i + 1) * 4096]) == c['pixelsSha256']
    depth = load(candidate / 'depth/browser-report.json'); depth_native_bytes = read(A / 'stage-gpu-stream-replay/depth-threshold/native.json')
    assert SHA(depth_native_bytes) == depth['nativeReportSha256']
    samples = next(r['samples'] for r in json.loads(depth_native_bytes)['rows'] if r['operation'] == 'copyD16')
    assert len(depth['reports']) == len(samples) == 915 and depth['differentDepthValues'] == 0
    assert depth['wasmSha256'] == load(candidate / 'depth/build.json')['wasmSha256']
    for c, n in zip(depth['reports'], samples): assert c['inputWord'] == n['inputWord'] and c['portable'] == c['d3d9'] == n['d16']
    for n in ['tools/th14-gpu-alpha-depth.html', 'tools/th14-stage-depth-quantization.html', 'tools/th14-stage-gpu-depth-trace-read.js', 'tools/th14-positive-w-viewport-candidate-oct19.html']: read(R / n)
    for n in ['color-result.jpg', 'uv-result.jpg', 'alpha-result.jpg', 'depth-result.jpg']: read(candidate / n)

    release_dir = A / 'positive-w-fixed20-depth-sdl-oct19'; release = load(release_dir / 'build.json')
    base = load(A / 'positive-w-viewport-sdl-oct19/build.json'); changed = []
    for group in ['sourceHashes', 'headerHashes']:
        for name, h in release[group].items():
            assert SHA(read(release_dir / 'source' / name)) == h
            if h != base[group][name]: changed.append(name)
    assert changed == ['portable/sdl/Renderer.cpp'] and release['sourceFiles'] == len(release['objectHashes']) == 146
    for name, h in release['objectHashes'].items(): assert SHA(read(release_dir / name)) == h
    assert release['importsUnchanged'] and release['exportsUnchanged']
    assert SHA(read(release_dir / 'th11.wasm')) == release['wasmSha256'] == '58eb0bbfa4363700a53b4ea6a520488b4974d40a8247a9fdf8a82ef45695d38a'
    assert SHA(read(release_dir / 'th11.mjs')) == release['loaderSha256']
    assert release['sourceHashes']['th12_web/cpp/game/ResourceCrypt.cpp'] == 'd57118f1114f3909c42a2e99e7df30e625f6563247a8118cd14bb9f68a0f97ef'
    for filename, folder in [('th14-launcher-runtime-fixed20-depth-oct19.json', 'out'), ('th14-launcher-site-fixed20-depth-oct19.json', 'site')]:
        report = load(R / 'docs/porting' / filename)
        for name, row in report['files'].items():
            b = read(Path(report[folder]) / name); assert len(b) == row['bytes'] and SHA(b) == row['sha256']
    browser = load(A / 'fixed20-depth-preview-oct19/observed.json')
    assert browser['oldReplayFilesVisible'] == 4 and browser['quietMarkerVisible'] and not browser['warningsAndErrors']
    assert browser['ordinaryReplayMenuUsed'] and browser['selectedStage'] == 2 and not browser['naturalReplayEofObserved']
    for n in ['four-replays-retained.jpg', 'stage2-running.jpg']: read(A / 'fixed20-depth-preview-oct19' / n)
    read(A / 'positive-w-fixed20-depth-adoption-oct19/receipt.json'); read(Path(__file__))
    return dict(evidenceVerified=True, changed=changed, sourceGameplayChanged=False, colorDifferencesBefore=451, colorDifferences=55, maxColorDelta=1, exactColorFrames=4, totalColorFrames=21, colorComparisons=colors, exactUv=47, nativeUvFullBytesCases=34, nativeUvHashOnlyCases=13, alphaCasesExact=2560, depthSamplesExact=915, sdlCompiledSources=146, wasmSha256=release['wasmSha256'], importsUnchanged=True, exportsUnchanged=True, completeGame=False, nativeEquivalent=False, scope='TH14/version10-only depth conversion supported by installed HAL samples. Retained full frames, UV and depth/alpha controls; 13 UV references and portable alpha controls are hash comparisons. No claim for arbitrary hardware, original ordinary-menu completion, visual RNG, shot lifetime, audio or whole-game equivalence. Historical Root-bound checkers retain their original versions.', bindings=bindings)


def main():
    p = argparse.ArgumentParser(); p.add_argument('--write', action='store_true'); p.add_argument('--check', action='store_true'); args = p.parse_args()
    assert args.write != args.check; result = inspect()
    if args.write:
        with OUT.open('x', encoding='utf-8') as f: json.dump(result, f, indent=2); f.write('\n')
    else: assert json.loads(OUT.read_bytes()) == result
    print(json.dumps(dict(evidenceVerified=True, colorDifferences=55, uvExact=47, alphaExact=2560, depthExact=915, bindings=len(result['bindings']), completeGame=False, nativeEquivalent=False)))


if __name__ == '__main__': main()
