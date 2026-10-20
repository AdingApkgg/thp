"""Recompute TH14 Native fog evidence and retained graphics controls."""
from pathlib import Path
import argparse, hashlib, json, math, struct

R = Path(__file__).resolve().parents[1]
A = R / 'artifacts/th14'
OUT = R / 'docs/porting/th14-native-fog-mix-observed-oct20.json'
SHA = lambda b: hashlib.sha256(b).hexdigest()


def inspect():
    bindings = {}

    def read(p):
        b = p.read_bytes(); bindings[p.relative_to(R).as_posix()] = dict(bytes=len(b), sha256=SHA(b)); return b

    def load(p): return json.loads(read(p))

    candidate = A / 'native-fog-mix-web-candidate-oct20'
    old = A / 'native-fog-web-candidate-v2-oct20'
    frozen = A / 'native-fog-sdl-oct20/source'
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
    text = renderer.decode()
    assert 'version==10&&p.fog&&!p.rangeFog&&p.fogMode==FogMode::Linear' in text
    assert 'volatile float range=p.fogFar-p.fogNear;volatile float scale=1.f/range;volatile float bias=p.fogFar*scale;' in text
    scalar=A/'native-fog-float-controls-oct20'; inputs=load(scalar/'inputs.json'); controls=load(scalar/'report.json')
    assert SHA(read(scalar/'inputs.json'))==controls['inputsSha256']
    assert SHA(read(A/'native-fog-float-controls-oct20.py'))==controls['toolSha256']
    assert SHA(read(R/'tools/th14-gpu-raster-native.py'))==controls['baseTypesSha256']
    assert SHA(read(A/'stage-gpu-stream-replay/prepared.json'))==inputs['preparedSha256']
    f32=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
    word=lambda x:struct.unpack('<I',struct.pack('<f',x))[0]
    value=lambda x:struct.unpack('<f',struct.pack('<I',x))[0]
    differences=dict(directDivision=0,madMultiplyBias=0,madDivisionBias=0)
    assert len(inputs['inputs'])==len(controls['rows'])==controls['cases']==240
    assert len({(r['near'],r['far']) for r in inputs['inputs']})==controls['pairs']==15
    for i,(n,c) in enumerate(zip(inputs['inputs'],controls['rows'])):
        assert c['index']==i and all(c[k]==n[k] for k in ('near','far','z'))
        near,far,z=[value(n[k]) for k in ('near','far','z')];span=f32(far-near);scale=f32(1./span)
        clamp=lambda x:min(1.,max(0.,x))
        models=dict(directDivision=word(clamp(f32(f32(far-abs(z))/span))),madMultiplyBias=word(clamp(f32(math.fma(-abs(z),scale,f32(far*scale))))),madDivisionBias=word(clamp(f32(math.fma(-abs(z),scale,f32(far/span))))))
        assert models==c['models'] and c['nativeWords'][0]==c['nativeWords'][1]==c['nativeWords'][2] and c['nativeWords'][3]==word(1.)
        for name,w in models.items():differences[name]+=int(w!=c['nativeWords'][0])
    assert differences==controls['differences']==dict(directDivision=129,madMultiplyBias=0,madDivisionBias=13)
    mix_cases=0
    for folder,count in [('native-fog-mix-controls-oct20',1920),('native-fog-mix-heldout-oct20',1200)]:
        d=A/folder; inputs=load(d/'inputs.json'); result=load(d/'report.json')
        assert SHA(read(d/'inputs.json'))==result['inputsSha256']
        assert SHA(read(A/(folder+'.py')))==result['toolSha256']
        assert len(inputs['inputs'])==len(result['rows'])==result['cases']==count
        assert not result['audioPlayed'] and not result['productionChanged']
        for i,(n,c) in enumerate(zip(inputs['inputs'],result['rows'])):
            assert c['index']==i and all(c[k]==n[k] for k in ('near','far','z','source','fog'))
            near,far,z=[value(n[k]) for k in ('near','far','z')];scale=f32(1./f32(far-near))
            factor=min(1.,max(0.,f32(math.fma(-abs(z),scale,f32(far*scale)))))
            source=[f32(((n['source']>>k)&255)/255.) for k in (16,8,0)]
            fog=[f32(((n['fog']>>k)&255)*f32(1./255.)) for k in (16,8,0)]
            expected=[word(f32(math.fma(color,factor,f32(math.fma(-background,factor,background))))) for color,background in zip(source,fog)]
            assert word(factor)==c['factorWord'] and expected==c['nativeWords'][:3] and c['nativeWords'][3]==word(1.)
            if count==1200:assert expected==c['models']['declaredNativeTwoMad']
        mix_cases+=count
    analysis=load(A/'native-fog-mix-controls-oct20/analysis.json')
    assert analysis['modelSelectionAfterObservation'] and analysis['rows'][0]['differentWords']==0
    read(A/'analyze-native-fog-mix-controls-oct20.py')
    assert 'vec3 rest=fogColor.rgb-fogColor.rgb*f;c.rgb=c.rgb*f+rest;' in text
    assert 'constexpr float reciprocal=1.f/255.f;' in text
    authored=A/'native-fog-vertex-v3-mad-oct20'; authored_report=load(authored/'native.json'); authored_bytes=read(authored/'native.bgra')
    assert SHA(authored_bytes)==authored_report['pixelsSha256']
    assert SHA(read(A/'capture-native-fog-vertex-controls-v3-oct20.py'))==authored_report['toolSha256']
    assert SHA(read(A/'stage-gpu-stream-replay/prepared.json'))==authored_report['preparedSha256']
    for pattern in ('*.asm','*.vso'):
        for path in sorted(authored.glob(pattern)):read(path)
    read(A/'native-fog-vertex-mad-oct20/failure.txt');read(A/'native-fog-vertex-v2-mad-oct20/native.json')

    native = load(A / 'stage-gpu-stream-replay/native.json'); native_bytes = read(A / 'stage-gpu-stream-replay/native.bgra')
    assert SHA(native_bytes) == native['pixelsSha256']
    assert authored_bytes == native_bytes and len(authored_report['frames']) == 21
    for n,a in zip(native['frames'],authored_report['frames']):
        assert all(n[k]==a[k] for k in ('stage','frame','offset','bytes'))
        assert SHA(authored_bytes[a['offset']:a['offset']+a['bytes']])==a['sha256']
    current = load(candidate / 'color/capture/report.json'); previous = load(old / 'color/capture/report.json')
    colors = []; new_channels = []
    assert len(current['reports']) == len(previous['reports']) == 21
    for n, p, c in zip(native['frames'], previous['reports'], current['reports']):
        expected = native_bytes[n['offset']:n['offset'] + n['bytes']]
        before = read(old / 'color/capture' / p['savedFile']); after = read(candidate / 'color/capture' / c['savedFile'])
        assert SHA(expected) == c['nativeSha256'] and SHA(before) == p['portableSha256'] and SHA(after) == c['portableSha256']
        diff = sum(x != y for x, y in zip(after, expected)); prior = sum(x != y for x, y in zip(before, expected))
        assert diff == c['differentChannels'] and diff <= prior
        assert max(abs(x - y) for x, y in zip(after, expected)) <= 1
        for i,(o,a,e) in enumerate(zip(before,after,expected)):
            if o==e and a!=e:new_channels.append(dict(stage=n['stage'],frame=n['frame'],x=(i//4)%640,y=(i//4)//640,channel=i%4,old=o,candidate=a,native=e))
        colors.append(dict(stage=n['stage'], frame=n['frame'], before=prior, after=diff))
    assert sum(x['before'] for x in colors) == 18 and sum(x['after'] for x in colors) == 1
    assert sum(x['after']==0 for x in colors)==20 and not new_channels
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

    release_dir = A / 'native-fog-mix-sdl-oct20'; release = load(release_dir / 'build.json')
    base = load(A / 'native-fog-sdl-oct20/build.json'); changed = []
    for group in ['sourceHashes', 'headerHashes']:
        for name, h in release[group].items():
            assert SHA(read(release_dir / 'source' / name)) == h
            if h != base[group][name]: changed.append(name)
    assert changed == ['portable/sdl/Renderer.cpp'] and release['sourceFiles'] == len(release['objectHashes']) == 146
    for name, h in release['objectHashes'].items(): assert SHA(read(release_dir / name)) == h
    assert release['importsUnchanged'] and release['exportsUnchanged']
    assert SHA(read(release_dir / 'th11.wasm')) == release['wasmSha256']
    assert SHA(read(release_dir / 'th11.mjs')) == release['loaderSha256']
    assert release['sourceHashes']['th12_web/cpp/game/ResourceCrypt.cpp'] == 'd57118f1114f3909c42a2e99e7df30e625f6563247a8118cd14bb9f68a0f97ef'
    for filename, folder in [('th14-launcher-runtime-native-fog-mix-oct20.json', 'out'), ('th14-launcher-site-native-fog-mix-oct20.json', 'site')]:
        report = load(R / 'docs/porting' / filename)
        for name, row in report['files'].items():
            b = read(Path(report[folder]) / name); assert len(b) == row['bytes'] and SHA(b) == row['sha256']
    browser = load(A / 'native-fog-mix-preview-oct20/observed.json')
    assert browser['oldReplayFilesVisible'] == 4 and browser['quietMarkerVisible'] and not browser['warningsAndErrors']
    assert browser['ordinaryReplayMenuUsed'] and browser['selectedStage'] == 2 and not browser['naturalReplayEofObserved']
    for n in ['four-replays-retained.jpg', 'stage2-running.jpg']: read(A / 'native-fog-mix-preview-oct20' / n)
    read(A / 'native-fog-mix-adoption-oct20/receipt.json'); read(Path(__file__))
    assert release['graphicsCandidateBuildSha256']==SHA(read(candidate/'color/build.json'))
    assert release['sourceHashes']['portable/sdl/Renderer.cpp']==SHA(renderer)
    return dict(evidenceVerified=True,changed=changed,sourceGameplayChanged=False,nativeAuthoredFramesExact=21,nativeFloatFogCases=240,nativeFloatFogDifferences=differences,nativeFogMixDiscoveryCases=1920,nativeFogMixHeldoutCases=1200,nativeFogMixRgbWords=9360,colorDifferencesBefore=18,colorDifferences=1,maxColorDelta=1,exactColorFrames=20,totalColorFrames=21,colorComparisons=colors,newDifferenceChannels=new_channels,exactUv=47,nativeUvFullBytesCases=34,nativeUvHashOnlyCases=13,alphaCasesExact=2560,depthSamplesExact=915,sdlCompiledSources=146,wasmSha256=release['wasmSha256'],importsUnchanged=True,exportsUnchanged=True,completeGame=False,nativeEquivalent=False,scope='Installed HAL linear non-range fog. Authored VS2 matches21 recorded direct-draw buffers;240 RGBA32F controls distinguish arithmetic. Web1 differing channel,max1,no new differing channels;Native mixed-conversion two-FMA formula matches9360 RGB words in discovery and predeclared held-out controls. Actual GLSL contraction has only the retained full-frame pixel evidence. UV34 original full-byte references and13 historical full hashes;portable alpha retains full hash only. No full retail framebuffer,arbitrary hardware,visual RNG,shot lifetime,physical audio or whole-game equivalence. Historical checkers preserved.',bindings=bindings)



def main():
    p = argparse.ArgumentParser(); p.add_argument('--write', action='store_true'); p.add_argument('--check', action='store_true'); args = p.parse_args()
    assert args.write != args.check; result = inspect()
    if args.write:
        with OUT.open('x', encoding='utf-8') as f: json.dump(result, f, indent=2); f.write('\n')
    else: assert json.loads(OUT.read_bytes()) == result
    print(json.dumps(dict(evidenceVerified=True, colorDifferences=1, uvExact=47, alphaExact=2560, depthExact=915, bindings=len(result['bindings']), completeGame=False, nativeEquivalent=False)))


if __name__ == '__main__': main()
