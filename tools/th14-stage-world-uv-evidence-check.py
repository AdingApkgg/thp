"""Verify authored UV diagnostics and Native combined-matrix controls."""
import hashlib,json,struct,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE='artifacts/th14/stage-gpu-stream-replay/';evidence={};sha=lambda b:hashlib.sha256(b).hexdigest()
def track(path):
    b=(ROOT/path).read_bytes();evidence[path]=dict(bytes=len(b),sha256=sha(b));return b
def read(path):return json.loads(track(path))
native=read(BASE+'world-uv/native.json');pixels=track(BASE+'world-uv/native.rgba32f');generation=read(BASE+'world-uv/generation.json');assert sha(pixels)==native['pixelsSha256'];assert len(pixels)==9830400
for key,path in [('generatorSha256','tools/th14-stage-world-uv-native.py'),('baseSourceSha256','tools/th14-stage-gpu-stream-hal.py'),('halSourceSha256','tools/th14-stage-world-uv-hal.py'),('shaderSha256',BASE+'world-uv/probe.pso'),('assemblySha256',BASE+'world-uv/probe.asm'),('nativeSha256',BASE+'world-uv/native.json')]:assert generation[key]==sha(track(path))
assert generation['compilerSha256']==sha(Path('C:/Windows/System32/d3dcompiler_47.dll').read_bytes());assert track(BASE+'world-uv/probe.asm').startswith(b'ps_2_0')
browser_reports=[]
for suffix,variant,mask_expected,uv_expected in [('production','world-uv-production',[1,3],[5608,32461]),('cpu-clip','world-uv-cpu-clip',[1,0],[5203,0])]:
    report=read(BASE+'world-uv/browser-'+suffix+'.json');build=read(BASE+'variants/'+variant+'/build.json');assert report['variant']==variant;assert report['nativePixelsSha256']==native['pixelsSha256'];assert build['toolSha256']==sha(track('tools/th14-stage-world-uv-build.mjs'));assert build['wasmSha256']==report['wasmSha256']==sha(track(BASE+'variants/'+variant+'/gpu.wasm'));assert build['loaderSha256']==sha(track(BASE+'variants/'+variant+'/gpu.mjs'))
    for path,h in build['sources'].items():assert h==sha(track(BASE+'variants/'+variant+'/'+path))
    assert build['baseBuildSha256']==sha(track(BASE+('build.json' if suffix=='production' else 'variants/cpu-clip-depth-fixed20/build.json')))
    summaries=[]
    for i,(nr,br) in enumerate(zip(native['frames'],report['reports'],strict=True)):
        assert (nr['stage'],nr['frame'],nr['originalDrawIndex'])==(br['stage'],br['frame'],br['originalDrawIndex']);raw=pixels[nr['offset']:nr['offset']+nr['bytes']];assert sha(raw)==nr['sha256']==br['nativeSha256']
        covered=sum(v[3]!=0 for v in struct.iter_unpack('<4f',raw));assert covered==br['nativeCovered'];assert covered==[2804,16235][i]
        assert br['coverageDifferences']==mask_expected[i];assert br['differentUV']==uv_expected[i]
        for d in br['uvFirst']:
            val=struct.unpack_from('<f',raw,(d['y']*640+d['x'])*16+d['channel']*4)[0];assert val==d['native'] and val!=d['portable']
        for d in br['maskFirst']:
            val=struct.unpack_from('<f',raw,(d['y']*640+d['x'])*16+12)[0];assert (val!=0)==d['native'] and d['native']!=d['portable']
        for p in br['selected']:assert list(struct.unpack_from('<4f',raw,(p['y']*640+p['x'])*16))==p['native']==[0,0,0,0]
        if suffix=='cpu-clip' and i==1:assert br['portableSha256']==nr['sha256']
        summaries.append(dict(frame=nr['frame'],nativeCovered=covered,portableCovered=br['portableCovered'],coverageDifferences=br['coverageDifferences'],differentUV=br['differentUV'],maxUVDelta=br['maxUVDelta'],strictPixelsEqual=br['portableSha256']==nr['sha256']))
    browser_reports.append(dict(variant=variant,frames=summaries))
for order,expected in [('separate',[(1,5203),(0,0)]),('pair',[(1,5203),(0,0)]),('reverse',[(0,0),(0,0)])]:
    variant='world-uv-clip-dot-'+order;prefix=BASE+'variants/'+variant+'/';report=read(prefix+'browser-result.json');build=read(prefix+'build.json');assert report['variant']==variant;assert report['nativePixelsSha256']==native['pixelsSha256'];assert build['toolSha256']==sha(track('tools/th14-stage-world-uv-dot-build.mjs'));assert build['baseBuildSha256']==sha(track(BASE+'variants/clip-dot-'+order+'/build.json'));assert build['fixtureBaseSha256']==sha(track(BASE+'variants/world-uv-cpu-clip/fixture.cpp'));assert build['wasmSha256']==report['wasmSha256']==sha(track(prefix+'gpu.wasm'));assert build['loaderSha256']==sha(track(prefix+'gpu.mjs'))
    for path,h in build['sources'].items():assert h==sha(track(prefix+path))
    summaries=[]
    for i,(nr,br) in enumerate(zip(native['frames'],report['reports'],strict=True)):
        assert (nr['stage'],nr['frame'])==(br['stage'],br['frame']);assert nr['sha256']==br['nativeSha256'];assert (br['coverageDifferences'],br['differentUV'])==expected[i]
        raw=pixels[nr['offset']:nr['offset']+nr['bytes']]
        for d in br['uvFirst']:assert struct.unpack_from('<f',raw,(d['y']*640+d['x'])*16+d['channel']*4)[0]==d['native']
        for d in br['maskFirst']:assert (struct.unpack_from('<f',raw,(d['y']*640+d['x'])*16+12)[0]!=0)==d['native']
        equal=expected[i]==(0,0)
        if equal:assert br['portableSha256']==nr['sha256']
        summaries.append(dict(frame=nr['frame'],coverageDifferences=br['coverageDifferences'],differentUV=br['differentUV'],maxUVDelta=br['maxUVDelta'],strictPixelsEqual=equal))
    browser_reports.append(dict(variant=variant,frames=summaries))
for mode in ('gpu-snap8','cpu-snap8'):
    variant='world-uv-viewport-'+mode;prefix=BASE+'variants/'+variant+'/';report=read(prefix+'browser-result.json');build=read(prefix+'build.json');assert report['variant']==variant;assert report['nativePixelsSha256']==native['pixelsSha256'];assert build['toolSha256']==sha(track('tools/th14-stage-world-viewport-build.mjs'));assert build['baseBuildSha256']==sha(track(BASE+'variants/world-uv-cpu-clip/build.json'));assert build['wasmSha256']==report['wasmSha256']==sha(track(prefix+'gpu.wasm'));assert build['loaderSha256']==sha(track(prefix+'gpu.mjs'))
    for path,h in build['sources'].items():assert h==sha(track(prefix+path))
    assert 'NVIDIA GeForce RTX 2080 Ti' in report['gpu']['renderer'] and 'Direct3D11' in report['gpu']['renderer']
    summaries=[]
    for nr,br in zip(native['frames'],report['reports'],strict=True):
        assert nr['sha256']==br['nativeSha256']==br['portableSha256'];assert br['coverageDifferences']==br['differentUV']==br['maxUVDelta']==0
        summaries.append(dict(frame=nr['frame'],coverageDifferences=0,differentUV=0,maxUVDelta=0,strictPixelsEqual=True))
    browser_reports.append(dict(variant=variant,gpu=report['gpu'],frames=summaries))
controls=[]
for mode,expected in [('float',[0,0]),('pair',[0,32470]),('double',[5611,32428]),('viewproj',[0,32355])]:
    prefix=BASE+'world-uv-native-'+mode+'/';g=read(prefix+'generation.json');n=read(prefix+'native.json');raw=track(prefix+'native.rgba32f');assert g['mode']==mode;assert g['generatorSha256']==sha(track('tools/th14-stage-world-uv-matrix-native.py'));assert g['baseSourceSha256']==sha(track('tools/th14-stage-world-uv-hal.py'));assert g['halSourceSha256']==sha(track('tools/th14-stage-world-uv-matrix-'+mode+'-hal.py'));assert g['ffpPixelsSha256']==native['pixelsSha256'];assert g['nativePixelsSha256']==n['pixelsSha256']==sha(raw);assert n['toolSha256']==g['halSourceSha256']
    track(prefix+'probe.vs.asm');track(prefix+'probe.vso');track(prefix+'probe.asm');track(prefix+'probe.pso');differences=[]
    for i,row in enumerate(n['frames']):
        a=raw[row['offset']:row['offset']+row['bytes']];b=pixels[row['offset']:row['offset']+row['bytes']];assert sha(a)==row['sha256'];words=sum(a[j:j+4]!=b[j:j+4] for j in range(0,len(a),4));coverage=sum(a[j+12:j+16]!=b[j+12:j+16] for j in range(0,len(a),16));assert words==expected[i];differences.append(dict(frame=row['frame'],differentFloatWords=words,coverageDifferences=coverage))
    assert differences==g['differences'];controls.append(dict(mode=mode,frames=differences))
if controls[0]['mode']=='float':assert all(r['differentFloatWords']==0 for r in controls[0]['frames'])
track('tools/th14-stage-world-uv.html');release=read('runtimes/th14/th14_web/artifacts/sdl3-release/build.json');assert release['sources']['portable/sdl/Renderer.cpp']==sha(track('runtimes/th12/portable/sdl/Renderer.cpp'));assert read(BASE+'build.json')['sources']['runtimes/th12/portable/sdl/Shaders.hpp']==sha(track('runtimes/th12/portable/sdl/Shaders.hpp'))
output=dict(diagnosticEvidenceVerified=True,strictPixelsEqual=False,productionChanged=False,completeGame=False,nativeEquivalent=False,browserVariants=browser_reports,nativeMatrixControls=controls,evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),scope='Two recorded world quads only. Native ps2 authored UV output with FFP vertices, alpha/depth/blend/fog disabled and other draws excluded. Authored vs2 float P*(V*W) m4x4 control has complete 9,830,400 output bytes identical to this FFP reference. CPU clip WebGL exactly matches the second complete RGBA32F frame, but first still fails coverage/UV. Incompatible earlier ps3 zero-UV fixtures are archived and excluded. Browser full portable float buffers are not independently archived; Native byte files, saved hashes and first discrepancies are checked. No complete-game/retail-framebuffer or production repair claim.')
(ROOT/'docs/porting/th14-stage-world-uv-observed-oct12.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(dict(diagnosticEvidenceVerified=True,browserVariants=browser_reports,nativeMatrixControls=controls)))
