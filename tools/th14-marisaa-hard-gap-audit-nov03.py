"""Independently retain every selected and camera mismatch in a finite Hard replay."""
from pathlib import Path
import array,collections,gzip,hashlib,importlib.util,json,struct,subprocess,sys
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/replay-alternatives-nov03/case-marisaa-hard';N=H/'native';M=H/'model';sha=lambda b:hashlib.sha256(b).hexdigest()
native=json.loads((N/'report.json').read_bytes());model=json.loads((M/'report.json').read_bytes());end=json.loads((H/'process-end.json').read_bytes());queue=json.loads((H/'queue-end.json').read_bytes());quiet=json.loads((H/'native-silence-verified.json').read_bytes())
assert native['callbacks']==model['callbacks']==75855 and native['recordedStages']==[1,2,3,4,5] and native['observedForcedReplayEndMenu'] and not native['replayTerminalMarkerObservationImplemented'] and native['childExited'] and not native['error']
assert end['exitCode']==0 and end['guardStop'] is None and end['actualMastersZero'] and quiet['verifiedActualNativeMasterLevelsZero'] and quiet['nativePid']==native['pid'] and not queue['strictPassed']
left=(N/'selected-state.u32').read_bytes();right=(M/'selected-state.u32').read_bytes();assert len(left)==len(right)==75855*128 and sha(left)==native['selectedSha256'];counts=collections.Counter();first={}
for n in range(75855):
 a=struct.unpack_from('<32I',left,n*128);b=struct.unpack_from('<32I',right,n*128)
 for j,(x,y) in enumerate(zip(a,b)):
  if x!=y:counts[str(j)]+=1;first.setdefault(str(j),{'index':n,'stage':a[30],'stageFrame':a[0],'native':x,'portable':y})
assert dict(counts)=={'21':1,'24':1} and all(v['index']==31382 and v['stage']==3 and v['stageFrame']==0 for v in first.values()) and model['differenceCounts']==dict(counts)
cam=(N/'world-camera.raw').read_bytes();portable=(M/'portable-camera.u32').read_bytes();offsets=[*range(0,88,4),0x104,0x108,0x10c];assert len(cam)==75855*0x124 and len(portable)==75855*25*4;cam_counts=collections.Counter();cam_first={}
for i in range(75855):
 for j,off in enumerate(offsets):
  a=struct.unpack_from('<I',cam,i*0x124+off)[0];b=struct.unpack_from('<I',portable,(i*25+j)*4)[0]
  if a!=b:cam_counts[str(j)]+=1;cam_first.setdefault(str(j),{'index':i,'native':a,'portable':b})
assert dict(cam_counts)=={'12':22137,'13':22137,'14':22137} and all(v['index']==48676 for v in cam_first.values())
assert (N/'hud-score.u32').read_bytes()==(M/'portable-hud.u32').read_bytes()
spec=importlib.util.spec_from_file_location('vm_fields',R/'tools/th14-hud-completion-evidence-check-oct25.py');vm=importlib.util.module_from_spec(spec);spec.loader.exec_module(vm);vmrows=0
for f in N.glob('live-vms-callback-*.json'):
 frame=int(f.stem.rsplit('-',1)[1]);
 if frame>75855:continue
 rows=json.loads(f.read_bytes())['rows'];actual=json.loads((M/f'portable-live-{frame}.json').read_bytes());blobs=[bytes.fromhex(x['rawVmHex']) for x in rows];handles={struct.unpack_from('<I',b,0x570)[0]:struct.unpack_from('<I',b,0x540)[0] for b in blobs};assert len(handles)==len(rows) and [vm.vm_words(b,handles) for b in blobs]==actual;vmrows+=len(rows)
index=json.loads((N/'combat-pool-index.json').read_bytes());checkpoints=0
for entry in index['snapshots']:
 if entry['callback']>75855:continue
 zipped=(N/'combat-pools'/entry['file']).read_bytes();assert sha(zipped)==entry['sha256'];obs=json.loads(gzip.decompress(zipped));actual=json.loads((M/f"combat-{entry['callback']}.json").read_bytes())
 for family,layout in index['fields'].items():
  expected=[]
  for row in obs['original'][family]:
   blob=bytes.fromhex(row['rawHex']);expected.append([row['slot'] if offset is None else struct.unpack_from('<H' if family=='bullets' and name=='state' else '<I',blob,offset)[0] for name,offset in layout])
  assert expected==actual['rows'][family],(entry['callback'],family)
 checkpoints+=1
allocation=[json.loads(x) for x in (N/'allocation-events.jsonl').read_bytes().splitlines()];cutoff=native['anmPublicationTraceCutoffPlayerCallbacks'];pub=json.loads((M/f'portable-allocations-initial-through-{cutoff}.json').read_bytes());assert [(x['handle'],x['file'],x['script']) for x in allocation]==[(x['handle'],x['file'],x['script']) for x in pub]
timing=H/'failed-case-timing-verified.json';p=subprocess.run([sys.executable,'-X','utf8',str(R/'tools/th14-verify-native-initialize-timing-v2-nov03.py'),'--native',str(N),'--model',str(M),'--output',str(timing)],capture_output=True);assert p.returncode==0,p.stderr
result={'passedGapAudit':True,'callbacks':75855,'recordedStages':[1,2,3,4,5],'sourceReplayEofProved':False,'strictPassed':False,'selectedDifferenceCounts':dict(counts),'selectedFirst':first,'cameraDifferenceCounts':dict(cam_counts),'cameraFirst':cam_first,'hudEqual':True,'sampledVmRowsEqual':vmrows,'combatCheckpointsEqual':checkpoints,'initialPublicationsEqual':len(pub),'observedInitializeTimingCoveragePassed':True,'nativeMastersZero':True,'nativeValuesProvidedToEngine':False,'productionChanged':False,'completeGame':False,'nativeEquivalent':False,'nativeReportSha256':sha((N/'report.json').read_bytes()),'modelReportSha256':sha((M/'report.json').read_bytes()),'toolSha256':sha(Path(__file__).read_bytes())}
(H/'gap-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
