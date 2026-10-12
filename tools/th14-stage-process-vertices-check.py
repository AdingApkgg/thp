from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/th14/stage-gpu-stream-replay';evidence={}
def read(p):
 b=(ROOT/p).read_bytes();evidence[p]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest());return b
sha=lambda b:hashlib.sha256(b).hexdigest()
rows=[]
for replay in [False,True]:
 prefix='artifacts/th14/stage-gpu-stream-replay/'+('process-vertices-no-fog-replay/' if replay else 'process-vertices/')
 report=json.loads(read(prefix+'report.json'));assert report['processedVertexReplay']==replay
 for key,p in [('generatorSha256','tools/th14-stage-process-vertices-native.py'),('parentSourceSha256','tools/th14-stage-gpu-stream-hal.py'),('halSourceSha256','tools/th14-stage-process-vertices-replay-hal.py' if replay else 'tools/th14-stage-process-vertices-hal.py')]:assert report[key]==sha(read(p))
 ref='artifacts/th14/stage-gpu-stream-replay/'+('variants/no-fog/' if replay else '')
 meta=json.loads(read(ref+'native.json'));frame=next(f for f in meta['frames'] if (f['stage'],f['frame'])==(3,599));all_ref=read(ref+'native.bgra');expected=all_ref[frame['offset']:frame['offset']+frame['bytes']];actual=read(prefix+'native.bgra');assert len(actual)==len(expected)==1228800
 assert sha(actual)==report['nativeSha256'];assert sha(expected)==report['referenceSha256'];count=sum(a!=b for a,b in zip(actual,expected));assert count==report['differentChannels']==(1 if replay else 0);assert report['instrumentationPreservesFinalFrame']==(not replay)
 assert len(report['captures'])==1;capture=report['captures'][0];assert capture['vertexCount']==4 and capture['drawIndex']==5 and capture['result']==0
 vertices=read(prefix+'processed-vertices.bin');assert len(vertices)==4*28;assert sha(vertices)==capture['sha256'];assert vertices==b''.join(int(w).to_bytes(4,'little') for w in capture['words'])
 differences=[dict(x=i//4%640,y=i//4//640,channel=i%4,actual=a,reference=b) for i,(a,b) in enumerate(zip(actual,expected)) if a!=b]
 rows.append(dict(processedVertexReplay=replay,capturedVertices=4,differentChannels=count,first=differences[:32],instrumentationPreservesFinalFrame=not replay))
out=dict(diagnosticEvidenceVerified=True,productionChanged=False,completeGame=False,nativeEquivalent=False,rows=rows,evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),scope='Independent hidden HAL ProcessVertices probe, one four-vertex draw. Original draw control exactly preserves complete original frame; returned-vertex no-fog replay has one color-channel difference, retained. This API does not establish actual raster vertex equivalence; no pixel repair or original-process framebuffer.')
(ROOT/'docs/porting/th14-stage-process-vertices-observed-oct13.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(diagnosticEvidenceVerified=True,rows=rows)))
