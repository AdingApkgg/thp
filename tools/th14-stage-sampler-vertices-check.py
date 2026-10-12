"""Bind all-vertex clip readbacks and independently evaluate arithmetic models."""
import hashlib,json,struct,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE='artifacts/th14/stage-gpu-stream-replay/';evidence={}
sha=lambda b:hashlib.sha256(b).hexdigest()
def track(p):
    b=(ROOT/p).read_bytes();evidence[p]=dict(bytes=len(b),sha256=sha(b));return b
def read(p):return json.loads(track(p))
def f32(v):return struct.unpack('<f',struct.pack('<f',v))[0]
def word(v):return struct.unpack('<I',struct.pack('<f',v))[0]
def value(w):return struct.unpack('<f',struct.pack('<I',w))[0]
prefix=BASE+'sampler-vertices/';g=read(prefix+'generation.json');n=read(prefix+'native.json');pixels=track(prefix+'samples.rgba32f');inputs=read(prefix+'clip-inputs.json');prepared=read(BASE+'prepared.json');b=read(prefix+'browser-result.json')
for key,path in [('wrapperSha256','tools/th14-stage-sampler-vertices-native.py'),('parentGeneratorSha256','tools/th14-stage-sampler-corners-native.py'),('generatorSha256','tools/th14-stage-sampler-vertices-generator.py'),('halSourceSha256','tools/th14-stage-sampler-vertices-hal.py'),('baseSourceSha256','tools/th14-stage-sampler-matrix-float-hal.py')]:assert g[key]==sha(track(path))
assert g['nativeSha256']==sha(track(prefix+'native.json'));assert g['sampleSha256']==n['pixelsSha256']==sha(pixels);assert len(pixels)==584*16
assert len(g['results'])==len(inputs)==len(b['reports'])==584
models={'fusedSequential':0,'separateSequential':0};seen={}
for i,(nr,br,inp) in enumerate(zip(g['results'],b['reports'],inputs,strict=True)):
    frame=next(f for f in prepared['frames'] if (f['stage'],f['frame'])==(nr['stage'],nr['frame']));draw=[d for d in frame['commands'] if d['kind']=='draw'][nr['draw']];stride=draw['stride']//4
    assert nr['sourceWords']==draw['words'][nr['corner']*stride:nr['corner']*stride+3]+[0x3f800000]
    key=(nr['stage'],nr['frame'],nr['draw']);seen.setdefault(key,set()).add(nr['corner'])
    assert nr['resultWords']==list(struct.unpack_from('<4I',pixels,i*16))==br['nativeWords']==br['portableWords'];assert nr['sourceWords']==br['sourceWords']==inp['sourceWords'];assert nr['matrixWords']==br['matrixWords']==inp['matrixWords'];assert (nr['stage'],nr['frame'],nr['draw'],nr['corner'])==(br['stage'],br['frame'],br['draw'],br['corner']);assert br['differentWords']==0
    matrix=list(map(value,nr['matrixWords']));v=list(map(value,nr['sourceWords']))
    for row in range(4):
        q=f32(matrix[row]*v[0]);separate=q
        for k in range(1,4):q=f32(math.fma(matrix[k*4+row],v[k],q));separate=f32(separate+f32(matrix[k*4+row]*v[k]))
        models['fusedSequential']+=word(q)!=nr['resultWords'][row];models['separateSequential']+=word(separate)!=nr['resultWords'][row]
for (stage,frame,index),corners in seen.items():
    f=next(f for f in prepared['frames'] if (f['stage'],f['frame'])==(stage,frame));d=[d for d in f['commands'] if d['kind']=='draw'][index];assert corners==set(range(len(d['words'])//(d['stride']//4)))
assert len(seen)==21;assert b['cases']==584 and b['floatWords']==2336 and b['differentWords']==0 and b['strictWordsEqual'];assert models['fusedSequential']==0
build_prefix=BASE+'variants/sampler-corners/';build=read(build_prefix+'build.json');assert b['nativeReportSha256']==sha(track(prefix+'generation.json'));assert b['wasmSha256']==build['wasmSha256']==sha(track(build_prefix+'gpu.wasm'));assert build['loaderSha256']==sha(track(build_prefix+'gpu.mjs'))
for p,h in build['sources'].items():assert h==sha(track(build_prefix+p))
for p in ['probe.vs.asm','probe.vso','probe.asm','probe.pso','inputs.json']:track(prefix+p)
track('tools/th14-stage-sampler-vertices.html')
out=dict(diagnosticEvidenceVerified=True,productionChanged=False,completeGame=False,nativeEquivalent=False,draws=21,vertices=584,floatWords=2336,differentWords=0,strictWordsEqual=True,arithmeticModels=models,evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),scope='Every submitted vertex of the 21 selected mismatch draws, including long strips. Native/browser constant-varying clip readback uses independent probe geometry and fixed input layout. Fused sequential dot products evaluated from captured binary32 inputs. Does not prove clipping, viewport, interpolation, full-frame pixels or whole-game equivalence.')
(ROOT/'docs/porting/th14-stage-sampler-vertices-observed-oct12.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['diagnosticEvidenceVerified','draws','vertices','floatWords','differentWords','arithmeticModels']}))
