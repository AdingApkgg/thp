"""Bind the rejected snap8 trial and explain full-buffer regressions."""
import hashlib,json,struct,math
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];evidence={}
sha=lambda b:hashlib.sha256(b).hexdigest()
def track(p):
    b=(ROOT/p).read_bytes();evidence[p]={'bytes':len(b),'sha256':sha(b)};return b
def read(p):return json.loads(track(p))
base=read('docs/porting/th14-stage-current-graphics-observed-oct14.json')
trial=read('docs/porting/th14-stage-current-world-snap8-observed-oct14.json')
assert base['diagnosticEvidenceVerified'] and trial['diagnosticEvidenceVerified']
assert base['sourceBindings']==trial['sourceBindings']
assert trial['comparisonToCurrentProduction']['baselineReportSha256']==sha(track('docs/porting/th14-stage-current-graphics-observed-oct14.json'))
for report in [base,trial]:
    for p,b in report['evidence'].items():assert sha(track(p))==b['sha256'],p
prepared=read('artifacts/th14/stage-gpu-stream-replay/prepared.json')
clips=read('artifacts/th14/stage-gpu-stream-replay/clip-dot-native-matrix/generation.json')['results']
native_ffp=track('artifacts/th14/stage-gpu-stream-replay/world-uv/native.rgba32f')
native_matrix=track('artifacts/th14/stage-gpu-stream-replay/world-uv-native-float/native.rgba32f')
assert native_ffp==native_matrix
assert sha(native_ffp)==read('artifacts/th14/stage-gpu-stream-replay/world-uv/native.json')['pixelsSha256']
assert sha(native_matrix)==read('artifacts/th14/stage-gpu-stream-replay/world-uv-native-float/native.json')['pixelsSha256']
f32=lambda v:struct.unpack('<f',struct.pack('<f',v))[0]
value=lambda v:struct.unpack('<f',struct.pack('<I',v))[0]
word=lambda v:struct.unpack('<I',struct.pack('<f',v))[0]
def multiply(a,b):
    out=[]
    for col in range(4):
        for row in range(4):
            q=f32(a[row]*b[col*4])
            for k in range(1,4):q=f32(q+f32(a[k*4+row]*b[col*4+k]))
            out.append(q)
    return out
def dot(a,v):
    out=[]
    for row in range(4):
        q=f32(a[row]*v[0])
        for k in range(1,4):q=f32(math.fma(a[k*4+row],v[k],q))
        out.append(q)
    return out
yy,xx=np.indices((480,640))
def coverage(v):
    mask=np.zeros((480,640),dtype=bool)
    for tri in [[0,1,2],[2,1,3]]:
        p=v[tri];d1,d2=p[1]-p[0],p[2]-p[0];area=d1[0]*d2[1]-d1[1]*d2[0];es=[]
        for i in range(3):
            a,b=p[i],p[(i+1)%3];e=(b[0]-a[0])*(yy-a[1])-(b[1]-a[1])*(xx-a[0]);es.append(e if area>0 else -e)
        mask|=(es[0]>=0)&(es[1]>=0)&(es[2]>=0)
    return mask
models=[]
for index in [21,22]:
    row=base['uv']['rows'][index];frame=next(f for f in prepared['frames'] if (f['stage'],f['frame'])==(row['stage'],row['frame']))
    matrices={k:[float(i%5==0) for i in range(16)] for k in [256,2,3]};draw_index=0;source=None
    for c in frame['initialState']+frame['commands']:
        if c['kind']=='transform' and c['key'] in matrices:matrices[c['key']]=list(map(value,c['words']))
        elif c['kind']=='draw':
            if draw_index==row['draw']:source=c;break
            draw_index+=1
    assert source and source['count']==2 and len(source['words'])//(source['stride']//4)==4
    vwm=multiply(matrices[2],matrices[256]);combined=multiply(matrices[3],vwm);qs=[];nested=[];stride=source['stride']//4
    for i in range(4):
        v=list(map(value,source['words'][i*stride:i*stride+3]))+[1.0]
        q=dot(combined,v);control=next(c for c in clips if (c['stage'],c['frame'],c['corner'])==(row['stage'],row['frame'],i))
        assert control['sourceWords']==source['words'][i*stride:i*stride+3]+[0x3f800000]
        assert list(map(word,q))==control['resultWords'];qs.append(q);nested.append(dot(matrices[3],dot(vwm,v)))
    native=np.frombuffer(native_ffp[(index-21)*640*480*16:(index-20)*640*480*16],dtype='<f4').reshape(480,640,4)[:,:,3]!=0
    before=track('artifacts/th14/stage-current-graphics-fe406-oct14/uv/capture/'+f'frame-{index:03d}.rgba32f')
    after=track('artifacts/th14/stage-current-world-snap8-fe406-oct14/uv/capture/'+f'frame-{index:03d}.rgba32f')
    assert before==after
    portable=np.frombuffer(before,dtype='<f4').reshape(480,640,4)[:,:,3]!=0;misses=np.argwhere(native!=portable)
    for mode,q in [('seqCombinedNativeMatched',np.array(qs)),('sourceNestedModelOnly',np.array(nested))]:
        raw=np.stack(((q[:,0]/q[:,3]+1)*320,(-q[:,1]/q[:,3]+1)*240),axis=1)
        for bits in [None,4,8]:
            vertices=raw if bits is None else np.rint(raw*(2**bits))/(2**bits);mask=coverage(vertices)
            edges=[]
            for y,x in misses:
                left=(vertices[2,0]-vertices[0,0])*(y-vertices[0,1])-(vertices[2,1]-vertices[0,1])*(x-vertices[0,0])
                right=(vertices[3,0]-vertices[1,0])*(y-vertices[1,1])-(vertices[3,1]-vertices[1,1])*(x-vertices[1,0])
                edges.append(dict(point=[int(x),int(y)],leftEdge=float(left),rightEdge=float(right),nativeCovered=bool(native[y,x]),portableCovered=bool(portable[y,x]),modelCovered=bool(mask[y,x])))
            models.append(dict(stage=row['stage'],frame=row['frame'],draw=row['draw'],composition=mode,viewportSnapBits=bits,vertices=vertices.tolist(),nativeCoverageDifferences=int((mask!=native).sum()),portableCoverageDifferences=int((mask!=portable).sum()),edgeValuesAtMisses=edges))
color=[]
for before,after in zip(base['color']['rows'],trial['color']['rows'],strict=True):
    assert (before['stage'],before['frame'])==(after['stage'],after['frame']) and before['nativeSha256']==after['nativeSha256']
    color.append(dict(stage=before['stage'],frame=before['frame'],beforeDifferentChannels=before['differentChannels'],afterDifferentChannels=after['differentChannels'],change=after['differentChannels']-before['differentChannels'],beforeMaxDelta=before['maxDelta'],afterMaxDelta=after['maxDelta']))
regressions=[r for r in color if r['change']>0];assert len(regressions)==6
output=dict(diagnosticEvidenceVerified=True,adopted=False,productionChanged=False,completeGame=False,nativeEquivalent=False,rejectionReasons=['Four real coverage misses remain unchanged in byte-identical quad UV outputs.','Primary complete UV matches fall from 10 to 5 and selected float-word differences rise from 95 to 146.','Six color frames regress despite the aggregate decrease from 3887 to 3627 differing channels.'],colorComparison=color,colorRegressions=regressions,coverageModels=models,evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),numpyVersion=np.__version__,scope='Whole-buffer failed trial assessment and uniform ideal CPU triangle-edge models. Combined clip vectors are computed from original matrices/vertices and match all 32 controlled Native clip words; no Native values injected into the model. Independent original FFP and authored seq-combined Native full UV controls agree on 9,830,400 bytes. Nested source model is only controlled CPU arithmetic, not actual uninstrumented production GPU readback. Neither ideal coverage nor small-case agreement establishes the GPU viewport formula. Advertised WebGL subpixelBits4 is not sufficient to predict the observed mask; naive snap4 predicts 10/6 Native coverage failures instead of actual 1/3.')
p=ROOT/'docs/porting/th14-stage-current-world-snap8-assessment-oct14.json';p.write_text(json.dumps(output,indent=2)+'\n',encoding='utf8')
print(json.dumps({'diagnosticEvidenceVerified':True,'adopted':False,'colorRegressions':len(regressions),'coverageModels':[{k:r[k] for k in ['frame','composition','viewportSnapBits','nativeCoverageDifferences','portableCoverageDifferences']} for r in models]}))
