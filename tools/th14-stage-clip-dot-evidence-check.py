"""Verify Native vs2/MOV and physical browser uniform-varying readbacks."""
import hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE='artifacts/th14/stage-gpu-stream-replay/';evidence={};sha=lambda b:hashlib.sha256(b).hexdigest()
def track(path):
    b=(ROOT/path).read_bytes();evidence[path]=dict(bytes=len(b),sha256=sha(b));return b
def read(path):return json.loads(track(path))
results=[]
for mode in ('matrix','mov-control'):
    prefix=BASE+'clip-dot-native-'+mode+'/';g=read(prefix+'generation.json');n=read(prefix+'native.json');pixels=track(prefix+'native.rgba32f');inputs=read(prefix+'inputs.json');b=read(prefix+'browser-result.json');v=BASE+'variants/clip-dot-webgl-'+mode+'/';build=read(v+'build.json')
    assert g['mode']==mode;assert g['generatorSha256']==sha(track('tools/th14-stage-clip-dot-native.py'));assert g['baseSourceSha256']==sha(track('tools/th14-stage-world-uv-matrix-float-hal.py'));assert g['halSourceSha256']==sha(track('tools/th14-stage-clip-dot-'+mode+'-hal.py'));assert g['nativeSha256']==sha(track(prefix+'native.json'));assert g['pixelsSha256']==n['pixelsSha256']==sha(pixels)
    assert len(pixels)==131072;assert len(inputs)==len(g['results'])==len(n['frames'])==len(b['reports'])==8
    track(prefix+'probe.vs.asm');track(prefix+'probe.vso');track(prefix+'probe.asm');track(prefix+'probe.pso');assert n['width']==n['height']==32
    assert build['toolSha256']==sha(track('tools/th14-stage-clip-dot-webgl-build.mjs'));assert build['baseBuildSha256']==sha(track(BASE+'variants/world-uv-cpu-clip/build.json'));assert build['wasmSha256']==b['wasmSha256']==sha(track(v+'gpu.wasm'));assert build['loaderSha256']==sha(track(v+'gpu.mjs'));assert b['nativeReportSha256']==sha(track(prefix+'generation.json'))
    for p,h in build['sources'].items():assert h==sha(track(v+p))
    different=0
    for nr,gr,inp,br in zip(n['frames'],g['results'],inputs,b['reports'],strict=True):
        raw=pixels[nr['offset']:nr['offset']+nr['bytes']];assert sha(raw)==nr['sha256'];words=list(struct.unpack_from('<4I',raw,(16*32+16)*16));assert words==gr['resultWords']==br['nativeWords'];assert inp['sourceWords']==gr['sourceWords']==br['sourceWords'];assert inp['matrixWords']==gr['matrixWords']==br['matrixWords'];assert (nr['stage'],nr['frame'],nr['corner'])==(br['stage'],br['frame'],br['corner']);assert br['differentWords']==sum(a!=b for a,b in zip(br['nativeWords'],br['portableWords'],strict=True));different+=br['differentWords']
        if mode=='mov-control':assert words==inp['sourceWords']
    assert different==b['differentWords']==0;assert b['strictWordsEqual'];results.append(dict(mode=mode,cases=8,floatWords=32,differentWords=0,strictWordsEqual=True))
track('tools/th14-stage-clip-dot.html');out=dict(diagnosticEvidenceVerified=True,completeGame=False,nativeEquivalent=False,productionChanged=False,results=results,evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),scope='Controlled constant varyings with independent NDC geometry, eight captured corners of two recorded world quads. Native vs2 m4x4 and browser pre-half-pixel clip outputs match32 float words; MOV controls also match32. Does not establish shader arithmetic for all vertices, viewport division/rasterization equivalence or a production fix. Native raw float framebuffers and browser complete32-word readbacks are independently compared.')
(ROOT/'docs/porting/th14-stage-clip-dot-observed-oct12.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(diagnosticEvidenceVerified=True,results=results)))
