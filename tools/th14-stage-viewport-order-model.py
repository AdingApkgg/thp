"""Compare uniform viewport associations against indirect Native plane estimates."""
import hashlib,json,math,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE='artifacts/th14/stage-gpu-stream-replay/';evidence={};sha=lambda b:hashlib.sha256(b).hexdigest()
def track(p):
 b=(ROOT/p).read_bytes();evidence[p]=dict(bytes=len(b),sha256=sha(b));return b
def read(p):return json.loads(track(p))
f32=lambda v:struct.unpack('<f',struct.pack('<f',v))[0]
models={'double-ratio':lambda x,w,h:(x/w+1)*h,'float-ratio-fma':lambda x,w,h:f32(math.fma(f32(x/w),h,h)),'float-ratio-separate':lambda x,w,h:f32(f32(f32(x/w)*h)+h),'sum-divide-scale':lambda x,w,h:f32(f32(f32(x+w)/w)*h),'sum-scale-divide':lambda x,w,h:f32(f32(f32(x+w)*h)/w),'homogeneous-fma-divide':lambda x,w,h:f32(f32(math.fma(x,h,f32(w*h)))/w),'homogeneous-separate-divide':lambda x,w,h:f32(f32(f32(x*h)+f32(w*h))/w),'sum-times-reciprocal-scale':lambda x,w,h:f32(f32(f32(x+w)*f32(1/w))*h),'sum-times-scaled-reciprocal':lambda x,w,h:f32(f32(x+w)*f32(h/w))}
clips=read(BASE+'sampler-vertices/generation.json')['results'];clips += [dict(c,draw=68 if c['frame']==599 else 45) for c in read(BASE+'clip-dot-native-matrix/generation.json')['results']];index={(c['stage'],c['frame'],c['draw'],c['corner']):c for c in clips};observed={}
for path in ['docs/porting/th14-stage-uv-plane-fit-observed-oct12.json','docs/porting/th14-stage-uv-strip-plane-fit-observed-oct12.json']:
 report=read(path)
 for tri in report['results']:
  for v in tri['vertices']:
   key=(tri.get('stage',report.get('stage')),tri.get('frame',report.get('frame')),tri.get('draw',report.get('draw')),v['corner']);xy=v['nearestSnap8XY'];assert key not in observed or observed[key]==xy;observed[key]=xy
results=[]
for name,fn in models.items():
 rows=[];different=0
 for key,xy in observed.items():
  q=index[key]['resultValues'];projected=[fn(q[0],q[3],320),fn(-q[1],q[3],240)];snap=[round(v*256)/256 for v in projected];n=sum(a!=b for a,b in zip(xy,snap));different+=n;rows.append(dict(stage=key[0],frame=key[1],draw=key[2],corner=key[3],nativeEstimatedSnap8=xy,modelSnap8=snap,differentCoordinates=n))
 results.append(dict(model=name,vertices=len(rows),differentCoordinates=different,rows=rows))
out=dict(diagnosticOnly=True,productionChanged=False,completeGame=False,nativeEquivalent=False,results=results,evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),scope='Uniform viewport expression associations evaluated from captured binary32 clip coordinates against inferred snap8 coordinates of 16 vertices. Plane estimates are indirect, not direct FFP positions; matching this small set does not establish a production formula or whole-game equivalence.')
(ROOT/'docs/porting/th14-stage-viewport-order-model-observed-oct12.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps([{k:r[k] for k in ['model','vertices','differentCoordinates']} for r in results]))
