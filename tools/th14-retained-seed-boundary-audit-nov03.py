"""Independently audit a retained seed-boundary comparison; preserve failed gates."""
from pathlib import Path
import argparse,array,gzip,hashlib,importlib.util,json,struct,subprocess,sys
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/replay-candidates-second-nov03/retained-seed-boundary-current';N=R/'artifacts/th14/stage3-seed-store-live-v2-nov01/native';M=H/'model';sha=lambda b:hashlib.sha256(b).hexdigest();native=json.loads((N/'report.json').read_bytes());model=json.loads((M/'report.json').read_bytes());assert native['callbacks']==model['callbacks']==26000 and native['childExited'] and not native['error'] and not native['debugErrors'] and model['diagnosticPrefixOnly'] and model['comparisonToolSha256']==sha((R/'tools/th14-compare-observed-seed-store-nov03.mjs').read_bytes()) and model['wasmSha256']=='f00a33cb9687fb544441d71bf9e5d78249b4d2e00d4059d59e7736ab1fb1c6eb'
events_raw=(N/'seed-store-instruction-events.jsonl').read_bytes();assert sha(events_raw)==native['seedStoreInstructionEventsSha256'];events=[json.loads(x) for x in events_raw.splitlines()];store=next(x for x in events if x['pc']==0x456129);phase=next(x for x in model['observedPhaseInputs'] if x['stage']==3 and x['phase']=='Initialize');assert store['readOnly'] and not store['providedToEngine'] and not store['threadSchedulingControlled'] and phase['readyNs']==store['hostMonotonicNs'] and phase['completionSource']=='original456129AfterScriptSeedBeforeVisualCounter_CompositeInitializationTimingNotProved'
state=(N/'selected-state.u32').read_bytes();assert sha(state)==native['selectedSha256'] and state==(M/'selected-state.u32').read_bytes();camera=(N/'world-camera.raw').read_bytes();offsets=[*range(0,88,4),0x104,0x108,0x10c];assert sha(camera)==native['worldCameraSha256'] and array.array('I',(struct.unpack_from('<I',camera,n*0x124+off)[0] for n in range(26000) for off in offsets)).tobytes()==(M/'portable-camera.u32').read_bytes();assert (N/'hud-score.u32').read_bytes()==(M/'portable-hud.u32').read_bytes()
spec=importlib.util.spec_from_file_location('vm_fields',R/'tools/th14-hud-completion-evidence-check-oct25.py');vm=importlib.util.module_from_spec(spec);spec.loader.exec_module(vm);fields=json.loads((M/'live-report.json').read_bytes())['fields'];differences=[];vmrows=0
for path in sorted(N.glob('live-vms-callback-*.json')):
 frame=int(path.stem.rsplit('-',1)[1]);rows=json.loads(path.read_bytes())['rows'];actual=json.loads((M/f'portable-live-{frame}.json').read_bytes());blobs=[bytes.fromhex(row['rawVmHex']) for row in rows];handles={struct.unpack_from('<I',blob,0x570)[0]:struct.unpack_from('<I',blob,0x540)[0] for blob in blobs};assert len(handles)==len(rows)==len(actual)
 for raw,observed in zip(blobs,actual):
  expected=vm.vm_words(raw,handles);assert len(expected)==len(observed)==len(fields)==303 and expected[0]==observed[0]
  for i,(x,y) in enumerate(zip(expected,observed)):
   if x!=y:differences.append((frame,fields[i]))
 vmrows+=len(rows)
assert differences.count((22000,'worldZ'))==3 and differences.count((24000,'worldZ'))==2 and len(differences)==5
index=json.loads((N/'combat-pool-index.json').read_bytes());checkpoints=0
for entry in index['snapshots']:
 if entry['callback']>26000:continue
 compressed=(N/'combat-pools'/entry['file']).read_bytes();assert sha(compressed)==entry['sha256'];observation=json.loads(gzip.decompress(compressed));actual=json.loads((M/f"combat-{entry['callback']}.json").read_bytes());assert (observation['callback'],observation['stage'],observation['stageFrame'])==(actual['callback'],actual['stage'],actual['stageFrame'])
 for family,layout in index['fields'].items():
  expected=[]
  for row in observation['original'][family]:
   blob=bytes.fromhex(row['rawHex']);expected.append([row['slot'] if off is None else struct.unpack_from('<H' if family=='bullets' and name=='state' else '<I',blob,off)[0] for name,off in layout])
  assert expected==actual['rows'][family]
 checkpoints+=1
publications=[json.loads(line) for line in (N/'allocation-events.jsonl').read_bytes().splitlines()];cutoff=native['anmPublicationTraceCutoffPlayerCallbacks'];portable=json.loads((M/f'portable-allocations-initial-through-{cutoff}.json').read_bytes());assert len(publications)==len(portable) and [(r['handle'],r['file'],r['script']) for r in publications]==[(r['handle'],r['file'],r['script']) for r in portable]
negative=H/'composite-init-must-not-pass.json';assert not negative.exists();p=subprocess.run([sys.executable,'-X','utf8',str(R/'tools/th14-verify-native-initialize-timing-nov03.py'),'--native',str(N),'--model',str(M),'--output',str(negative)],cwd=R,capture_output=True);assert p.returncode!=0 and b'unverified Initialize timestamp' in p.stderr and not negative.exists()
result=dict(verifiedFiniteRetainedRawAudit=True,callbacks=26000,observedSeedStoreInstruction='0x456129',compositeInitializationTimingProved=False,selectedStateCameraHudAndCombatEqual=True,combatCheckpoints=checkpoints,orderedPublications=len(publications),vmRowsCompared=vmrows,vmDifferentWords=len(differences),vmDifferenceLocations=[dict(callback=22000,field='worldZ',count=3),dict(callback=24000,field='worldZ',count=2)],strictInitializeGateRejected=True,strictPassed=False,actualOldRecordingOrderRecovered=False,nativeValuesProvidedToEngine=False,completeGame=False,nativeEquivalent=False,nativeReportSha256=sha((N/'report.json').read_bytes()),modelReportSha256=sha((M/'report.json').read_bytes()),toolSha256=sha(Path(__file__).read_bytes()))
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path,default=R/'docs/porting/th14-retained-seed-boundary-audit-nov03.json');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(H) or out.is_relative_to(R/'docs/porting');data=(json.dumps(result,indent=2)+'\n').encode()
if a.check:assert out.read_bytes()==data
else:assert not out.exists();out.write_bytes(data)
print(json.dumps(result))
