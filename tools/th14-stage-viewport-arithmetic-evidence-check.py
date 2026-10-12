import hashlib,json,struct,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE='artifacts/th14/stage-gpu-stream-replay/';evidence={};sha=lambda b:hashlib.sha256(b).hexdigest()
def track(p):
 b=(ROOT/p).read_bytes();evidence[p]=dict(bytes=len(b),sha256=sha(b));return b
def read(p):return json.loads(track(p))
f32=lambda v:struct.unpack('<f',struct.pack('<f',v))[0];word=lambda v:struct.unpack('<I',struct.pack('<f',v))[0]
prefix=BASE+'viewport-arithmetic/';g=read(prefix+'generation.json');n=read(prefix+'native.json');pixels=track(prefix+'samples.rgba32f');clips=read(BASE+'sampler-vertices/generation.json');b=read(prefix+'browser-result.json')
assert g['generatorSha256']==sha(track('tools/th14-stage-viewport-arithmetic-native.py'));assert g['baseSourceSha256']==sha(track('tools/th14-stage-sampler-vertices-hal.py'));assert g['halSourceSha256']==sha(track('tools/th14-stage-viewport-arithmetic-hal.py'));assert g['nativeSha256']==sha(track(prefix+'native.json'));assert g['sampleSha256']==n['pixelsSha256']==sha(pixels);assert g['clipReferenceSha256']==sha(track(BASE+'sampler-vertices/generation.json'));assert len(pixels)==584*16
div_dif=0;mad_dif=0;snap_dif=0
for i,(nr,br,c) in enumerate(zip(g['results'],b['reports'],clips['results'],strict=True)):
 assert nr['resultWords']==list(struct.unpack_from('<4I',pixels,i*16))==br['nativeWords']==br['portableWords'];assert nr['sourceWords']==br['sourceWords']==c['sourceWords'];assert nr['matrixWords']==br['matrixWords']==c['matrixWords'];assert nr['clipWords']==c['resultWords'];assert (nr['stage'],nr['frame'],nr['draw'],nr['corner'])==(br['stage'],br['frame'],br['draw'],br['corner']);assert br['differentWords']==0
 q=c['resultValues'];reciprocal=f32(1/q[3]);xy=[f32(math.fma(f32(q[0]/q[3]),320,320)),f32(math.fma(f32(q[1]/q[3]),-240,240))];assert word(reciprocal)==nr['divisionReciprocalWord'];assert list(map(word,xy))==nr['divisionViewportWords'];div_dif+=word(reciprocal)!=nr['nativeWords'][2];mad_dif+=sum(word(v)!=nr['nativeWords'][j] for j,v in enumerate(xy));snap_dif+=sum(round(v*256)!=round(nr['nativeValues'][j]*256) for j,v in enumerate(xy))
assert (div_dif,mad_dif,snap_dif)==(g['reciprocalDifferentWords'],g['viewportDifferentWords'],g['snap8DifferentCoordinates'])==(82,174,6)
assert b['cases']==584 and b['floatWords']==2336 and b['differentWords']==0 and b['strictWordsEqual'];assert b['nativeReportSha256']==sha(track(prefix+'generation.json'))
bp=BASE+'variants/viewport-arithmetic/';build=read(bp+'build.json');assert build['toolSha256']==sha(track('tools/th14-stage-viewport-arithmetic-build.mjs'));assert build['baseBuildSha256']==sha(track(BASE+'variants/sampler-corners/build.json'));assert b['wasmSha256']==build['wasmSha256']==sha(track(bp+'gpu.wasm'));assert build['loaderSha256']==sha(track(bp+'gpu.mjs'))
for p,h in build['sources'].items():assert h==sha(track(bp+p))
for p in ['probe.vs.asm','probe.vso','probe.asm','probe.pso','clip-inputs.json','inputs.json']:track(prefix+p)
track('tools/th14-stage-viewport-arithmetic.html')
out=dict(diagnosticEvidenceVerified=True,productionChanged=False,completeGame=False,nativeEquivalent=False,vertices=584,floatWords=2336,differentWords=0,strictWordsEqual=True,cpuDivisionDifferentReciprocals=82,cpuDivisionDifferentViewportWords=174,cpuDivisionDifferentSnap8Coordinates=6,evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),scope='Authored vs2 m4x4/rcp/mul/mad constant varying and WebGL equivalent arithmetic with controlled geometry. All readback words match; CPU division differs. Does not recover or prove original FFP viewport, raster interpolation or whole-game equivalence.')
(ROOT/'docs/porting/th14-stage-viewport-arithmetic-control-observed-oct12.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['diagnosticEvidenceVerified','vertices','floatWords','differentWords','cpuDivisionDifferentSnap8Coordinates']}))
