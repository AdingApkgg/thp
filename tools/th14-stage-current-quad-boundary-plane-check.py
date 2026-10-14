"""Independent full-buffer UV-plane and boundary analysis; never changes runtime.

Recovered coordinates are indirect estimates conditioned by rounded pixel UVs.
Native and portable use identical common-covered samples. No estimated value
is submitted to either renderer and no failed comparison is masked.
"""
import hashlib,json,struct,math
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];evidence={}
sha=lambda b:hashlib.sha256(b).hexdigest()
def track(p):
    b=(ROOT/p).read_bytes();evidence[p]={'bytes':len(b),'sha256':sha(b)};return b
def read(p):return json.loads(track(p))
BASE='artifacts/th14/stage-current-graphics-fe406-oct14/'
COMBINED='artifacts/th14/stage-current-sequential-clip-fe406-oct14/'
cases=read(BASE+'uv-cases.json');baseline=read(BASE+'uv/capture/report.json');combined=read(COMBINED+'uv/capture/report.json')
assert baseline['sourceBindings']==combined['sourceBindings']
for p in [BASE+'sources.json',COMBINED+'sources.json',BASE+'uv/build.json',COMBINED+'uv/build.json']:read(p)
native_ffp=read('artifacts/th14/stage-gpu-stream-replay/world-uv/native.json')
native_bytes=track('artifacts/th14/stage-gpu-stream-replay/world-uv/native.rgba32f');assert sha(native_bytes)==native_ffp['pixelsSha256']
assert native_bytes==track('artifacts/th14/stage-gpu-stream-replay/world-uv-native-float/native.rgba32f')
clips=read('artifacts/th14/stage-gpu-stream-replay/clip-dot-native-matrix/generation.json')['results']
y,x=np.indices((480,640));results=[];whole_masks=[]
def mask_from_vertices(vertices):
    mask=np.zeros((480,640),bool)
    for tri in [[0,1,2],[2,1,3]]:
        p=vertices[tri];d1,d2=p[1]-p[0],p[2]-p[0];area=d1[0]*d2[1]-d1[1]*d2[0];edges=[]
        for i in range(3):
            a,b=p[i],p[(i+1)%3];edge=(b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0]);edges.append(edge if area>0 else -edge)
        mask|=(edges[0]>=0)&(edges[1]>=0)&(edges[2]>=0)
    return mask
for index in [21,22]:
    case=cases['cases'][index];key='/'.join(map(str,[case['stage'],case['frame'],case['originalDrawIndex']]));binding=next(v for v in cases['fullBindings'] if v['key']==key)
    raw=track(binding['path'])[binding['offset']:binding['offset']+binding['bytes']];assert sha(raw)==case['nativeSha256']
    arrays={'Native':np.frombuffer(raw,dtype='<f4').reshape(480,640,4)}
    for name,prefix,report in [('production',BASE,baseline),('sequentialCombined',COMBINED,combined)]:
        raw=track(prefix+'uv/capture/'+f'frame-{index:03d}.rgba32f');assert sha(raw)==report['reports'][index]['portableSha256'];assert report['reports'][index]['nativeSha256']==case['nativeSha256']
        arrays[name]=np.frombuffer(raw,dtype='<f4').reshape(480,640,4)
    n=arrays['Native'];common=np.logical_and.reduce([p[:,:,3]==1 for p in arrays.values()]);estimated={name:{} for name in arrays}
    for tri in [[0,1,2],[2,1,3]]:
        mask=common&((n[:,:,0]+n[:,:,1]<1-1e-4) if tri==[0,1,2] else(n[:,:,0]+n[:,:,1]>1+1e-4));xx=x[mask]/640;yy=y[mask]/480;one=np.ones_like(xx);zero=np.zeros_like(xx);fits=[]
        assert len(xx)>40
        for name,p in arrays.items():
            uu=p[:,:,0][mask].astype(float);vv=p[:,:,1][mask].astype(float)
            matrix=np.vstack((np.column_stack((xx,yy,one,zero,zero,zero,-uu*xx,-uu*yy)),np.column_stack((zero,zero,zero,xx,yy,one,-vv*xx,-vv*yy))))
            rhs=np.concatenate((uu,vv));coeff,_,rank,svals=np.linalg.lstsq(matrix,rhs,rcond=None);assert rank==8
            aa,bb,cc,dd,ee,ff,gg,hh=coeff;den=gg*xx+hh*yy+1;fu=(aa*xx+bb*yy+cc)/den;fv=(dd*xx+ee*yy+ff)/den;vertices=[]
            for i in tri:
                cu,cv=[(0,0),(1,0),(0,1),(1,1)][i];pos=np.linalg.solve([[aa-cu*gg,bb-cu*hh],[dd-cv*gg,ee-cv*hh]],[cu-cc,cv-ff])*[640,480];snap=np.rint(pos*256)/256
                if i in estimated[name]:assert estimated[name][i]==snap.tolist()
                estimated[name][i]=snap.tolist();vertices.append(dict(corner=i,estimatedXY=pos.tolist(),nearestSnap8XY=snap.tolist(),distanceToSnap8=(pos-snap).tolist()))
            fits.append(dict(mode=name,vertices=vertices,maxUVResidual=float(max(abs(fu-uu).max(),abs(fv-vv).max())),conditionNumber=float(svals[0]/svals[-1]),samples=len(xx)))
        results.append(dict(index=index,stage=case['stage'],frame=case['frame'],draw=case['originalDrawIndex'],triangle=tri,fits=fits))
    for name,coordinates in estimated.items():
        vertices=np.array([coordinates[i] for i in range(4)]);mask=mask_from_vertices(vertices)
        row=dict(index=index,stage=case['stage'],frame=case['frame'],draw=case['originalDrawIndex'],modelFrom=name,vertices=vertices.tolist(),coverageDifferences={k:int((mask!=(p[:,:,3]!=0)).sum()) for k,p in arrays.items()})
        assert row['coverageDifferences'][name]==0;whole_masks.append(row)
f32=lambda v:struct.unpack('<f',struct.pack('<f',v))[0]
arithmetic=[]
for control in clips:
    q=control['resultValues'];assert list(struct.unpack('<4I',struct.pack('<4f',*q)))==control['resultWords']
    for axis,half in [(0,320),(1,240)]:
        a=q[axis] if axis==0 else -q[axis];w=q[3]
        modes={'doubleProjection':(a/w+1)*half,'floatNormalizedFirst':f32(f32(f32(a/w)*0.5)+0.5)*(half*2),'floatRatioFMA':f32(math.fma(f32(a/w),half,half)),'homogeneousScaledReciprocal':f32(f32(a+w)*f32(half/w)),'homogeneousReciprocalScale':f32(f32(f32(a+w)*f32(1/w))*half)}
        arithmetic.append(dict(stage=control['stage'],frame=control['frame'],corner=control['corner'],axis=axis,clipNumerator=a,clipW=w,models={k:dict(value=v,nearestSnap8=round(v*256)/256) for k,v in modes.items()}))
critical=next(r for r in arithmetic if (r['frame'],r['corner'],r['axis'])==(599,2,0))
assert critical['models']['floatNormalizedFirst']['value']==665.400390625
assert critical['models']['floatNormalizedFirst']['nearestSnap8']==665.3984375
assert critical['models']['floatRatioFMA']['nearestSnap8']==critical['models']['homogeneousScaledReciprocal']['nearestSnap8']==665.40234375
out=dict(diagnosticEvidenceVerified=True,productionChanged=False,completeGame=False,nativeEquivalent=False,planeFits=results,inferredWholeMaskControls=whole_masks,uniformViewportArithmetic=arithmetic,criticalThreshold=critical,evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),numpyVersion=np.__version__,scope='Indirect rational-plane fits on identical common-covered full-buffer UV pixels, followed by ideal uniform triangle-edge evaluation. Inferred snap8 corners reconstruct every complete observed Native/production/sequential mask for the two quads. These noise-conditioned estimates are not direct GPU vertex readback and are never used as runtime corrections. Uniform CPU viewport arithmetic models use captured controlled Native clip words only as offline inputs; they do not establish actual production shader execution or GPU viewport behavior. The original Native FFP and authored sequential-combined Native UV buffers agree on 9,830,400 bytes.')
p=ROOT/'docs/porting/th14-stage-current-quad-boundary-plane-observed-oct14.json';p.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps({'diagnosticEvidenceVerified':True,'wholeMasks':whole_masks,'criticalThreshold':critical}))
