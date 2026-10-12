"""Test uniform bilinear-weight models against captured native UV/sample pairs."""
import hashlib,json,struct,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE='artifacts/th14/stage-gpu-stream-replay/';evidence={}
sha=lambda b:hashlib.sha256(b).hexdigest()
def track(p):
 b=(ROOT/p).read_bytes();evidence[p]=dict(bytes=len(b),sha256=sha(b));return b
def read(p):return json.loads(track(p))
def f32(v):return struct.unpack('<f',struct.pack('<f',v))[0]
def word(v):return struct.unpack('<I',struct.pack('<f',v))[0]
p=read(BASE+'prepared.json');uv=read(BASE+'sampler-uv/native.json');raw=read(BASE+'sampler-raw/native.json')
track(BASE+'sampler-uv/samples.rgba32f');track(BASE+'sampler-raw/samples.rgba32f')
textures={t['handle']:t for t in p['textures']};cache={};cases=[]
for u,r in zip(uv['frames'],raw['frames'],strict=True):
 assert (u['stage'],u['frame'],u['originalDrawIndex'],u['texture'])==(r['stage'],r['frame'],r['originalDrawIndex'],r['texture'])
 t=textures[u['texture']]
 if t['format']!=21:continue
 if t['handle'] not in cache:
  data=track(BASE+t['file']);assert sha(data)==t['sha256'];cache[t['handle']]=data
 frame=next(f for f in p['frames'] if (f['stage'],f['frame'])==(u['stage'],u['frame']));sampler={1:1,2:1};index=0
 for c in frame['initialState']+frame['commands']:
  if c['kind']=='samplerState' and c['sampler']==0:sampler[c['key']]=c['value']
  if c['kind']=='draw':
   if index==u['originalDrawIndex']:break
   index+=1
 assert sampler[1]==sampler[2]==1
 for us,rs in zip(u['samples'],r['samples'],strict=True):
  assert (us['x'],us['y'])==(rs['x'],rs['y']);assert us['values'][3]==1
  cases.append((t,us,rs))
results=[]
for bits,rounding,arithmetic,conversion in [(None,'none','double','exact')]+[(bits,rounding,arithmetic,'exact') for bits in (8,9,10,12) for rounding in ('even','floor') for arithmetic in ('double','float','fused')]+[(bits,'even',arithmetic,'half') for bits in (8,9,10) for arithmetic in ('double','float','fused')]:
 different=0;max_delta=0;first=[]
 for t,u,r in cases:
  coords=[f32(f32(u['values'][i]*t[['width','height'][i]])-.5) for i in (0,1)];xy=[math.floor(v) for v in coords];weights=[v-i for v,i in zip(coords,xy)]
  if bits is not None:weights=[(round(v*(1<<bits)) if rounding=='even' else math.floor(v*(1<<bits)))/(1<<bits) for v in weights]
  pixels=[];data=cache[t['handle']]
  for dx,dy in ((0,0),(1,0),(0,1),(1,1)):
   at=((xy[1]+dy)%t['height'])*t['pitch']+((xy[0]+dx)%t['width'])*4;b,g,rr,a=data[at:at+4];pixels.append([struct.unpack('<e',struct.pack('<e',v/255))[0] if conversion=='half' else v/255 for v in (rr,g,b,a)])
  values=[]
  for channel in range(4):
   a,b,c,d=[v[channel] for v in pixels];x,y=weights
   if arithmetic=='double':v=(a*(1-x)+b*x)*(1-y)+(c*(1-x)+d*x)*y
   else:
    a,b,c,d=map(f32,(a,b,c,d))
    lerp=(lambda a,b,w:f32(math.fma(f32(b-a),w,a))) if arithmetic=='fused' else (lambda a,b,w:f32(f32(a*f32(1-w))+f32(b*w)))
    v=lerp(lerp(a,b,x),lerp(c,d,x),y)
   values.append(f32(v))
  for i,v in enumerate(values):
   different+=word(v)!=r['words'][i];max_delta=max(max_delta,abs(v-r['values'][i]))
  if len(first)<8 and any(word(v)!=r['words'][i] for i,v in enumerate(values)):first.append(dict(texture=t['handle'],x=u['x'],y=u['y'],uv=u['values'][:2],weights=weights,predicted=values,native=r['values']))
 results.append(dict(weightBits=bits,rounding=rounding,arithmetic=arithmetic,texelConversion=conversion,samples=len(cases),floatWords=len(cases)*4,differentWords=different,maxDelta=max_delta,first=first))
out=dict(diagnosticOnly=True,productionChanged=False,completeGame=False,nativeEquivalent=False,results=results,evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),scope='BGRA8 textures only; native authored UV and texture-sample outputs at the same selected points. Uniform CPU weight models, no fitted per-pixel correction. Separate shader captures may expose different interpolation rounding; model agreement would not prove the hardware sampler implementation.')
(ROOT/'docs/porting/th14-stage-sampler-weight-model-observed-oct12.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps([{k:r[k] for k in ['weightBits','rounding','arithmetic','texelConversion','samples','differentWords','maxDelta']} for r in results]))
