"""Estimate rational UV planes from archived Native RGBA32F frame readbacks."""
import hashlib,json,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE='artifacts/th14/stage-gpu-stream-replay/';evidence={};sha=lambda b:hashlib.sha256(b).hexdigest()
def track(p):
 b=(ROOT/p).read_bytes();evidence[p]=dict(bytes=len(b),sha256=sha(b));return b
def read(p):return json.loads(track(p))
n=read(BASE+'world-uv/native.json');raw=track(BASE+'world-uv/native.rgba32f');cases=[]
for frame in n['frames']:
 data=raw[frame['offset']:frame['offset']+frame['bytes']];assert sha(data)==frame['sha256'];cases.append((frame,data))
w=read(BASE+'sampler-uv-worst/native.json');data=track(BASE+'sampler-uv-worst/full.rgba32f');assert sha(data)==w['frames'][0]['fullFloatFrameSha256'];cases.append((w['frames'][0],data))
clip=read(BASE+'sampler-vertices/generation.json');extra=read(BASE+'clip-dot-native-matrix/generation.json');clip['results'] += [dict(c,draw=68 if c['frame']==599 else 45) for c in extra['results']];results=[]
for frame,data in cases:
 pixels=np.frombuffer(data,dtype='<f4').reshape(480,640,4);y,x=np.indices((480,640));u=pixels[:,:,0].astype(np.float64);v=pixels[:,:,1].astype(np.float64);covered=pixels[:,:,3]==1
 corners=[c for c in clip['results'] if (c['stage'],c['frame'],c['draw'])==(frame['stage'],frame['frame'],frame['originalDrawIndex'])];assert len(corners)==4
 for triangle in ((0,1,2),(2,1,3)):
  mask=covered&((u+v<1-1e-4) if triangle==(0,1,2) else (u+v>1+1e-4));xx=x[mask]/640;yy=y[mask]/480;uu=u[mask];vv=v[mask];assert len(xx)>40
  one=np.ones_like(xx);zero=np.zeros_like(xx);a=np.vstack((np.column_stack((xx,yy,one,zero,zero,zero,-uu*xx,-uu*yy)),np.column_stack((zero,zero,zero,xx,yy,one,-vv*xx,-vv*yy))));rhs=np.concatenate((uu,vv));coeff,_,rank,_=np.linalg.lstsq(a,rhs,rcond=None);assert rank==8
  aa,bb,cc,dd,ee,ff,gg,hh=coeff;den=gg*xx+hh*yy+1;fitted_u=(aa*xx+bb*yy+cc)/den;fitted_v=(dd*xx+ee*yy+ff)/den;vertices=[]
  for corner in triangle:
   uv=((0,0),(1,0),(0,1),(1,1))[corner];cu,cv=uv;pos=np.linalg.solve([[aa-cu*gg,bb-cu*hh],[dd-cv*gg,ee-cv*hh]],[cu-cc,cv-ff]);sx,sy=pos*np.array([640,480]);snap=np.round(np.array([sx,sy])*256)/256;vertices.append(dict(corner=corner,estimatedXY=[float(sx),float(sy)],nearestSnap8XY=snap.tolist(),distanceToSnap8=(np.array([sx,sy])-snap).tolist(),denominatorAtVertex=float(gg*pos[0]+hh*pos[1]+1),clipW=corners[corner]['resultValues'][3]))
  results.append(dict(stage=frame['stage'],frame=frame['frame'],draw=frame['originalDrawIndex'],triangle=triangle,samples=len(xx),coefficients=coeff.tolist(),maxUVResidual=float(max(np.max(np.abs(fitted_u-uu)),np.max(np.abs(fitted_v-vv)))),vertices=vertices))
out=dict(diagnosticOnly=True,productionChanged=False,completeGame=False,nativeEquivalent=False,results=results,evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),numpyVersion=np.__version__,scope='Least-squares rational-plane estimates from rounded Native float UV output for three actual quads. Pixel centers use D3D9 integer coordinates. Estimates are indirect and noise-conditioned; nearest-grid coordinates are not direct GPU viewport readback. No fitted per-pixel correction or production change.')
(ROOT/'docs/porting/th14-stage-uv-plane-fit-observed-oct12.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(results))
