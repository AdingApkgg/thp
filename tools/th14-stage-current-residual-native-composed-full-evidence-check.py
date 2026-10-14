"""Independently verify complete original FFP vs derived-matrix HAL buffers."""
import hashlib,json,struct
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];evidence={}
BASE='artifacts/th14/stage-gpu-stream-replay/'
FFP='artifacts/th14/stage-current-residual-native-uv-fe406-oct14/'
OUT='artifacts/th14/stage-current-residual-native-composed-uv-fe406-oct14/'
sha=lambda b:hashlib.sha256(b).hexdigest()
def track(p):
    path=Path(p);path=path if path.is_absolute() else ROOT/path;b=path.read_bytes();evidence[str(p)]={'bytes':len(b),'sha256':sha(b)};return b
def read(p):return json.loads(track(p))
pre=read(OUT+'preflight.json');completion=read(OUT+'capture-complete.json');native=read(OUT+'native.json');ffp=read(FFP+'native.json');prepared=read(BASE+'prepared.json')
assert pre['adapterToolSha256']==completion['toolSha256']==sha(track('tools/th14-stage-current-residual-native-composed-full-capture.py'))
assert pre['originalHelperSha256']==sha(track(pre['originalHelperPath']))=='c687b408fa4ba02f98da1b4ea3524ea5044045a0d54b2660e1a3b8b0bc7a690e'
assert pre['adaptedHelperSha256']==native['toolSha256']==sha(track(OUT+'capture-hal.py'))
assert completion['originalFFPReportSha256']==sha(track(FFP+'native.json'))
assert completion['composedReportSha256']==sha(track(OUT+'native.json')) and completion['preflightSha256']==sha(track(OUT+'preflight.json'))
for p,b in pre['bindings'].items():assert sha(track(p))==b['sha256'] and len(track(p))==b['bytes'],p
assert native['preparedSha256']==ffp['preparedSha256']==sha(track(BASE+'prepared.json'))
assert native['typesSha256']==ffp['typesSha256']==sha(track('tools/th14-gpu-raster-native.py'))
loaded=read(OUT+'loaded-d3d9.json');assert Path(loaded['path']).resolve()==Path('C:/Windows/System32/d3d9.dll').resolve()
assert loaded['sha256']==native['d3d9Sha256']==ffp['d3d9Sha256']==sha(track(loaded['path'])) and loaded['hiddenWindowStyle']==0
for file,key in [('probe.pso','compiledPS2Sha256'),('probe.vso','compiledVS2Sha256')]:assert pre[key]==sha(track(OUT+file))==sha(track(BASE+'sampler-matrix-float/'+file))
for file in ['probe.asm','probe.vs.asm']:assert track(OUT+file)==track(BASE+'sampler-matrix-float/'+file)
source=track(OUT+'capture-hal.py').decode('utf8')
assert "MODE='float'" in source and 'multiply(matrices[3],multiply(matrices[2],matrices[256]))' in source
assert 'def multiply(a,b):' in source and 'for tvalue in terms[1:]:v=f32(v+f32(tvalue))' in source
assert 'd3dcompiler' not in source and 'subprocess' not in source
assert track(OUT+'probe.vs.asm')==b'vs_2_0\ndcl_position v0\ndcl_texcoord v1\ndef c8,1,0,1,0\nm4x4 oPos,v0,c0\nmov r0,v1\nmov r0.zw,c8\nm4x4 oT0,r0,c4\n'

def multiply(a,b):
    a=np.array(a,dtype=np.float32).reshape(4,4).T;b=np.array(b,dtype=np.float32).reshape(4,4).T;r=np.empty((4,4),np.float32)
    for row in range(4):
        for col in range(4):
            s=np.float32(a[row,0]*b[0,col])
            for k in range(1,4):s=np.float32(s+np.float32(a[row,k]*b[k,col]))
            r[row,col]=s
    return r.T.reshape(-1)
rows=[];total=0
for i,(nr,fr) in enumerate(zip(native['frames'],ffp['frames'])):
    assert (nr['stage'],nr['frame'],nr['originalDrawIndex'])==(fr['stage'],fr['frame'],fr['originalDrawIndex'])
    n=track(OUT+f'frame-{i:03d}.rgba32f');f=track(FFP+f'frame-{i:03d}.rgba32f');assert len(n)==len(f)==640*480*16
    assert sha(n)==nr['fullFloatFrameSha256'] and sha(f)==fr['fullFloatFrameSha256'];assert n==f and nr['samples']==fr['samples']
    for sample in nr['samples']:assert list(struct.unpack_from('<4I',n,(sample['y']*640+sample['x'])*16))==sample['words']
    frame=next(frame for frame in prepared['frames'] if (frame['stage'],frame['frame'])==(nr['stage'],nr['frame']));matrices={};di=0
    for command in frame['initialState']+frame['commands']:
        if command['kind']=='transform':matrices[command['key']]=struct.unpack('<16f',struct.pack('<16I',*command['words']))
        elif command['kind']=='draw':
            if di==nr['originalDrawIndex']:break
            di+=1
    computed=multiply(matrices[3],multiply(matrices[2],matrices[256]));words=list(struct.unpack('<16I',computed.tobytes()))
    assert words==nr['computedClipMatrixWords'];total+=len(n)
    rows.append(dict(stage=nr['stage'],frame=nr['frame'],draw=nr['originalDrawIndex'],bytes=len(n),nativeFFPSha256=sha(f),derivedMatrixVSSha256=sha(n),differentFloatWords=0,coverageDifferences=0,originalMatricesUsed=True,computedClipMatrixWords=words,samples=len(nr['samples'])))
assert total==completion['fullBufferBytes']==14745600 and completion['allFFPFullHashesAndSamplesMatch'] and completion['caseMatches']==[True]*3
assert track(OUT+'samples.rgba32f')==track(FFP+'samples.rgba32f') and len(track(OUT+'samples.rgba32f'))==18*16
out=dict(diagnosticEvidenceVerified=True,productionChanged=False,completeGame=False,nativeEquivalent=False,originalFFPAndDerivedMatrixCompleteBytesEqual=True,completeComparedBytes=total,completeComparedFloatWords=total//4,differentFloatWords=0,coverageDifferences=0,physicalSamplePoints=18,rows=rows,evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),numpyVersion=np.__version__,scope='Three complete original-input hidden HAL RGBA32F controls. The real frozen original world/view/projection matrices are recomposed in separated-product/sum binary32 k0..3 order as P*(V*W), then processed by the existing own compiled Native m4x4 VS2 and PS2 UV probes. Complete bytes equal independent Native FFP buffers, not only selected samples. No captured/fitted clip coordinates, explicit snapping, retail process, visible UI or production changes. This rules out this CPU composition path for these residual controls; it does not identify actual GLSL matrix-vector or viewport arithmetic.')
(ROOT/'docs/porting/th14-stage-current-residual-native-composed-full-observed-oct14.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps({key:out[key] for key in ['diagnosticEvidenceVerified','completeComparedBytes','completeComparedFloatWords','differentFloatWords','coverageDifferences']}))
