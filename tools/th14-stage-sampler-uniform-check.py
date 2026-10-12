"""Independently bind controlled constant-UV sampler equality."""
import hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE='artifacts/th14/stage-gpu-stream-replay/';evidence={};sha=lambda b:hashlib.sha256(b).hexdigest()
def track(p):
 b=(ROOT/p).read_bytes();evidence[p]=dict(bytes=len(b),sha256=sha(b));return b
def read(p):return json.loads(track(p))
prefix=BASE+'sampler-uniform/';g=read(prefix+'generation.json');n=read(prefix+'native.json');inputs=read(prefix+'inputs.json');pixels=track(prefix+'samples.rgba32f');uv=read(BASE+'sampler-uv/native.json');b=read(prefix+'browser-result.json')
assert g['generatorSha256']==sha(track('tools/th14-stage-sampler-uniform-native.py'));assert g['baseSourceSha256']==sha(track('tools/th14-stage-sampler-corners-hal.py'));assert g['halSourceSha256']==sha(track('tools/th14-stage-sampler-uniform-hal.py'));assert g['nativeSha256']==sha(track(prefix+'native.json'));assert g['sampleSha256']==n['pixelsSha256']==sha(pixels);assert g['uvReferenceSha256']==sha(track(BASE+'sampler-uv/native.json'));assert pixels==track(BASE+'sampler-raw/samples.rgba32f')
uv_samples=[s for row in uv['frames'] for s in row['samples']];assert len(g['results'])==len(b['reports'])==len(inputs['cases'])==len(uv_samples)==102
for i,(nr,br,inp,u) in enumerate(zip(g['results'],b['reports'],inputs['cases'],uv_samples,strict=True)):
 assert nr['sourceWords']==inp['uvWords']==u['words']==br['sourceWords'];assert nr['originalPoint']==[u['x'],u['y']];assert nr['resultWords']==list(struct.unpack_from('<4I',pixels,i*16))==br['nativeWords']==br['portableWords'];assert (nr['stage'],nr['frame'],nr['draw'],nr['corner'])==(br['stage'],br['frame'],br['draw'],br['corner']);assert nr['matrixWords']==br['matrixWords'];assert br['differentWords']==0;assert list(struct.unpack('<4f',struct.pack('<4I',*br['portableWords'])))==br['portableValues']
assert b['cases']==102 and b['floatWords']==408 and b['differentWords']==0 and b['strictWordsEqual'];assert b['nativeReportSha256']==sha(track(prefix+'generation.json'))
build_prefix=BASE+'variants/sampler-uniform/';build=read(build_prefix+'build.json');assert build['toolSha256']==sha(track('tools/th14-stage-sampler-uniform-build.mjs'));assert build['baseBuildSha256']==sha(track(BASE+'variants/sampler-corners/build.json'));assert b['wasmSha256']==build['wasmSha256']==sha(track(build_prefix+'gpu.wasm'));assert build['loaderSha256']==sha(track(build_prefix+'gpu.mjs'))
for p,h in build['sources'].items():assert h==sha(track(build_prefix+p))
for p in ['probe.vs.asm','probe.vso','probe.asm','probe.pso','clip-inputs.json']:track(prefix+p)
track('tools/th14-stage-sampler-uniform.html');prepared=read(BASE+'prepared.json')
for t in prepared['textures']:assert t['sha256']==sha(track(BASE+t['file']))
out=dict(diagnosticEvidenceVerified=True,productionChanged=False,completeGame=False,nativeEquivalent=False,samples=102,floatWords=408,differentWords=0,strictWordsEqual=True,nativeConstantSamplesEqualOriginalSamples=True,evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),scope='Captured native UV words applied to independent constant-varying geometry. All408 native/browser sampler words equal and native constant sampling equals the previously archived original-geometry samples. This excludes the sampler as the source of these selected differences with these textures/states; does not prove all sampling configurations, raster interpolation or whole-game equivalence.')
(ROOT/'docs/porting/th14-stage-sampler-uniform-observed-oct12.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['diagnosticEvidenceVerified','samples','floatWords','differentWords','nativeConstantSamplesEqualOriginalSamples']}))
