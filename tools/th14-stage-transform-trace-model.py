"""Check recorded instrumented-position Z/W against uniform float dot models."""
import hashlib,json,struct,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE='artifacts/th14/stage-gpu-stream-replay/';evidence={};sha=lambda b:hashlib.sha256(b).hexdigest()
def track(p):
 b=(ROOT/p).read_bytes();evidence[p]=dict(bytes=len(b),sha256=sha(b));return b
def read(p):return json.loads(track(p))
f32=lambda v:struct.unpack('<f',struct.pack('<f',v))[0];word=lambda v:struct.unpack('<I',struct.pack('<f',v))[0];value=lambda w:struct.unpack('<f',struct.pack('<I',w))[0]
def multiply(a,b):
 out=[]
 for col in range(4):
  for row in range(4):
   v=f32(a[row]*b[col*4])
   for k in range(1,4):v=f32(v+f32(a[k*4+row]*b[col*4+k]))
   out.append(v)
 return out
prepared=read(BASE+'prepared.json');trace=read(BASE+'variants/clip-transform-trace/browser-result.json');parent=read(BASE+'variants/cpu-clip-depth-fixed20/browser-current-control.json');old=read(BASE+'variants/cpu-clip-depth-fixed20/browser-result.json');assert all(a['portableSha256']==b['portableSha256'] for a,b in zip(parent['reports'],old['reports'],strict=True));frame_dif=sum(a['portableSha256']!=b['portableSha256'] for a,b in zip(trace['reports'],parent['reports'],strict=True))
raw_positions=track(BASE+'variants/clip-transform-trace/positions.f32');assert raw_positions==b''.join(struct.pack('<'+str(len(c['words']))+'I',*c['words']) for r in trace['reports'] for c in r['transformCaptures'])
models={'fusedSequential':dict(zwDifferentWords=0,xyDifferentWords=0,fusedHalfPixelDifferentWords=0,maxZWDelta=0),'separateSequential':dict(zwDifferentWords=0,xyDifferentWords=0,fusedHalfPixelDifferentWords=0,maxZWDelta=0)};vertices=0;draws=0;screen_vertices=0;first=[]
for frame,report in zip(prepared['frames'],trace['reports'],strict=True):
 assert (frame['stage'],frame['frame'])==(report['stage'],report['frame']);matrices={k:[float(i%5==0) for i in range(16)] for k in (256,2,3,16)};fvf=0x102;viewport=(640,480);draw_index=0
 for cmd in frame['initialState']+frame['commands']:
  if cmd['kind']=='transform':matrices[cmd['key']]=list(map(value,cmd['words']))
  elif cmd['kind']=='fvf':fvf=cmd['value']
  elif cmd['kind']=='viewport':viewport=cmd['words'][2:4]
  elif cmd['kind']=='draw':
   capture=report['transformCaptures'][draw_index];draw_index+=1;draws+=1;assert (capture['drawIndex'],capture['count'],capture['stride'])==(draw_index-1,cmd['count'],cmd['stride']);stride=cmd['stride']//4
   if fvf==0x102 and cmd['count']==2:indices=list(range(4))
   else:
    indices=[0,1,2]
    for i in range(1,cmd['count']):indices += [i+1,i,i+2] if i&1 else [i,i+1,i+2]
   assert capture['vertexCount']==len(indices);assert len(capture['words'])==len(indices)*4
   if fvf==0x44:screen_vertices+=len(indices);continue
   matrix=multiply(matrices[3],multiply(matrices[2],matrices[256]))
   for at,index in enumerate(indices):
    v=list(map(value,cmd['words'][index*stride:index*stride+3]))+[1];actual=capture['words'][at*4:at*4+4];vertices+=1
    for model in models:
     q=[]
     for row in range(4):
      acc=f32(matrix[row]*v[0])
      for k in range(1,4):acc=f32(math.fma(matrix[k*4+row],v[k],acc)) if model=='fusedSequential' else f32(acc+f32(matrix[k*4+row]*v[k]))
      q.append(acc)
     predicted=[f32(q[0]+f32(q[3]/viewport[0])),f32(-q[1]+f32(q[3]/viewport[1])),q[2],q[3]];n=sum(word(predicted[k])!=actual[k] for k in (2,3));models[model]['zwDifferentWords']+=n;models[model]['xyDifferentWords']+=sum(word(predicted[k])!=actual[k] for k in (0,1));models[model]['maxZWDelta']=max(models[model]['maxZWDelta'],max(abs(predicted[k]-value(actual[k])) for k in (2,3)))
     half_fused=[f32(math.fma(q[3],f32(1/viewport[0]),q[0])),f32(math.fma(q[3],f32(1/viewport[1]),-q[1]))];models[model]['fusedHalfPixelDifferentWords']+=sum(word(half_fused[k])!=actual[k] for k in (0,1))
     if model=='fusedSequential' and n and len(first)<24:first.append(dict(stage=frame['stage'],frame=frame['frame'],draw=draw_index-1,vertex=index,predictedWords=list(map(word,predicted)),actualWords=actual))
 assert draw_index==len(report['transformCaptures'])==frame['directDraws']
assert draws==1005
bp=BASE+'variants/clip-transform-trace/';build=read(bp+'build.json');assert build['toolSha256']==sha(track('tools/th14-stage-transform-trace-build.mjs'));assert build['wasmSha256']==trace['wasmSha256']==sha(track(bp+'gpu.wasm'));assert build['loaderSha256']==sha(track(bp+'gpu.mjs'));assert build['baseBuildSha256']==sha(track(BASE+'variants/cpu-clip-depth-fixed20/build.json'))
for p,h in build['sources'].items():assert h==sha(track(bp+p))
out=dict(diagnosticEvidenceVerified=True,productionChanged=False,completeGame=False,nativeEquivalent=False,baselineReproduced=True,instrumentationPreservesFinalFrames=frame_dif==0,changedFinalFrames=frame_dif,draws=draws,worldVertices=vertices,screenVerticesExcluded=screen_vertices,models=models,firstZWDiscrepancies=first,evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),scope='Instrumented WebGL program position outputs with a discarded point draw followed by original raster topology. Original baseline repeated and all frame hashes matched its previous run; instrumented color frames differ, so these positions cannot be attributed to the uninstrumented program. CPU dot models are diagnostics, not Native position readback.')
(ROOT/'docs/porting/th14-stage-transform-trace-model-observed-oct12.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['diagnosticEvidenceVerified','baselineReproduced','changedFinalFrames','draws','worldVertices','models']}))
