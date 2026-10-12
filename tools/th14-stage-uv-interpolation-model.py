"""Recompute perspective interpolation from captured vertices, not pixel fitting."""
import hashlib,json,struct,math,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE='artifacts/th14/stage-gpu-stream-replay/';evidence={};sha=lambda b:hashlib.sha256(b).hexdigest()
def track(p):
 b=(ROOT/p).read_bytes();evidence[p]=dict(bytes=len(b),sha256=sha(b));return b
def read(p):return json.loads(track(p))
f32=lambda v:struct.unpack('<f',struct.pack('<f',v))[0];word=lambda v:struct.unpack('<I',struct.pack('<f',v))[0];value=lambda w:struct.unpack('<f',struct.pack('<I',w))[0]
prepared=read(BASE+'prepared.json');uv=read(BASE+'sampler-uv/native.json');clips=read(BASE+'sampler-vertices/generation.json');vp=read(BASE+'viewport-arithmetic/generation.json');clip_index={(c['stage'],c['frame'],c['draw'],c['corner']):c for c in clips['results']};vp_index={(c['stage'],c['frame'],c['draw'],c['corner']):c for c in vp['results']};results=[]
def clipped_polygon(tri,model):
 polygon=[(v[3],v[1]) for v in tri]
 planes=[lambda q:q[0]+q[3],lambda q:q[3]-q[0],lambda q:q[1]+q[3],lambda q:q[3]-q[1]]
 if 'depth' in model:planes=[lambda q:q[2],lambda q:q[3]-q[2]]
 if 'six' in model:planes += [lambda q:q[2],lambda q:q[3]-q[2]]
 for plane in planes:
  output=[]
  if not polygon:break
  for a,b in zip(polygon,polygon[1:]+polygon[:1]):
   da,db=plane(a[0]),plane(b[0]);inside_a,inside_b=da>=0,db>=0
   if inside_a:output.append(a)
   if inside_a!=inside_b:
    t=da/(da-db)
    if 'float' in model:t=f32(f32(da)/f32(da-db))
    lerp=lambda x,y:f32(math.fma(f32(y-x),t,x)) if 'float' in model else x+(y-x)*t
    output.append(([lerp(x,y) for x,y in zip(a[0],b[0])],[lerp(x,y) for x,y in zip(a[1],b[1])]))
  polygon=output
 out=[]
 for q,texture_uv in polygon:
  xy=[f32(math.fma(f32(q[0]/q[3]),320,320)),f32(math.fma(f32(q[1]/q[3]),-240,240))];xy=[round(v*256)/256 for v in xy];out.append((xy,texture_uv,1/q[3],q))
 return out
for position_model in ('division-fma-snap8','authored-rcp-mad-snap8','homogeneous-sum-snap8','scaled-reciprocal-snap8','clip-depth-double-snap8','clip-depth-float-snap8','clip-xy-double-snap8','clip-xy-float-snap8','clip-six-double-snap8','clip-six-float-snap8'):
 for reciprocal_model in (('double-division',) if position_model.startswith('clip-') else ('double-division','float-division','authored-rcp')):
  samples=[];different=0;maximum=0;uncovered=0
  for row in uv['frames']:
   frame=next(f for f in prepared['frames'] if (f['stage'],f['frame'])==(row['stage'],row['frame']));matrix=[float(i%5==0) for i in range(16)];texture_transform=True;draw_index=0
   for cmd in frame['initialState']+frame['commands']:
    if cmd['kind']=='transform' and cmd['key']==16:matrix=list(map(value,cmd['words']))
    if cmd['kind']=='textureStageState' and cmd['stage']==0 and cmd['key']==24:texture_transform=cmd['value']!=0
    if cmd['kind']=='draw':
     if draw_index==row['originalDrawIndex']:draw=cmd;break
     draw_index+=1
   stride=draw['stride']//4;vertices=[]
   for corner in range(len(draw['words'])//stride):
    key=(row['stage'],row['frame'],row['originalDrawIndex'],corner);q=clip_index[key]['resultValues'];native_vp=vp_index[key]['nativeValues'];xy=[f32(math.fma(f32(q[0]/q[3]),320,320)),f32(math.fma(f32(q[1]/q[3]),-240,240))] if position_model=='division-fma-snap8' else native_vp[:2]
    if position_model=='homogeneous-sum-snap8':xy=[f32(f32(f32(q[0]+q[3])*f32(1/q[3]))*320),f32(f32(f32(q[3]-q[1])*f32(1/q[3]))*240)]
    if position_model=='scaled-reciprocal-snap8':xy=[f32(f32(q[0]+q[3])*f32(320/q[3])),f32(f32(q[3]-q[1])*f32(240/q[3]))]
    xy=[round(v*256)/256 for v in xy]
    source=list(map(value,draw['words'][corner*stride+stride-2:corner*stride+stride]));transformed=source
    if texture_transform:
     v=source+[1,0];transformed=[]
     for r in range(2):
      acc=f32(matrix[r]*v[0])
      for k in range(1,4):acc=f32(math.fma(matrix[k*4+r],v[k],acc))
      transformed.append(acc)
    inv=1/q[3] if reciprocal_model=='double-division' else f32(1/q[3]) if reciprocal_model=='float-division' else native_vp[2];vertices.append((xy,transformed,inv,q))
   triangles=[]
   for i in range(len(vertices)-2):
    ids=(i,i+1,i+2);polygon=clipped_polygon([vertices[k] for k in ids],position_model) if position_model.startswith('clip-') else [vertices[k] for k in ids]
    for j in range(1,len(polygon)-1):triangles.append((ids,[polygon[0],polygon[j],polygon[j+1]]))
   for sample in row['samples']:
    found=None
    for ids,tri in triangles:
     a=np.array([[v[0][0] for v in tri],[v[0][1] for v in tri],[1,1,1]])
     if abs(np.linalg.det(a))<1e-12:continue
     bary=np.linalg.solve(a,[sample['x'],sample['y'],1])
     if min(bary)<-1e-7:continue
     weights=bary*np.array([v[2] for v in tri]);actual=[f32(sum(weights[k]*tri[k][1][c] for k in range(3))/sum(weights)) for c in (0,1)];found=(ids,actual)
    if found is None:uncovered+=1;continue
    ids,actual=found;delta=max(abs(actual[c]-sample['values'][c]) for c in (0,1));d=sum(word(actual[c])!=sample['words'][c] for c in (0,1));different+=d;maximum=max(maximum,delta);samples.append(dict(stage=row['stage'],frame=row['frame'],draw=row['originalDrawIndex'],x=sample['x'],y=sample['y'],triangle=ids,native=sample['values'][:2],model=actual,differentWords=d,maxDelta=delta))
  results.append(dict(positionModel=position_model,reciprocalModel=reciprocal_model,samples=len(samples),uncovered=uncovered,differentWords=different,maxDelta=maximum,reports=samples))
out=dict(diagnosticOnly=True,productionChanged=False,completeGame=False,nativeEquivalent=False,results=results,evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),numpyVersion=np.__version__,scope='Ideal double-precision barycentric perspective calculation from captured clip/UV words and uniform snap8 rules; no fitted per-pixel adjustment. Native authored reciprocal values are a diagnostic control, not a production lookup. Rounded Native UV outputs may reflect internal raster/plane arithmetic; model failures are retained.')
(ROOT/'docs/porting/th14-stage-uv-interpolation-model-observed-oct12.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps([{k:r[k] for k in ['positionModel','reciprocalModel','samples','uncovered','differentWords','maxDelta']} for r in results]))
