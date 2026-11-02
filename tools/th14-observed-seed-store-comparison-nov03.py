"""Independently inspect a new read-only original seed-store observation and two portable replays."""
from pathlib import Path
import array,gzip,hashlib,importlib.util,json,struct,subprocess,sys
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/stage3-worker-entry-vm-retry-nov03';N=H/'native';M=H/'compare-baseline/model';OTHER=H/'compare-seed-store/model';sha=lambda b:hashlib.sha256(b).hexdigest()
native=json.loads((N/'report.json').read_bytes());model=json.loads((M/'report.json').read_bytes());other=json.loads((OTHER/'report.json').read_bytes());capture=json.loads((H/'verified.json').read_bytes());assert capture['passed'] and capture['callbacks']==26000 and not capture['matchedStageObjectSnapshots']
assert model['callbacks']==other['callbacks']==26000 and model['diagnosticPrefixOnly'] and native['hardwareBreakpointsOnly'] and not native['rngOrCounterWrites']
phase=next(x for x in model['observedPhaseInputs'] if x['stage']==3 and x['phase']=='Initialize');other_phase=next(x for x in other['observedPhaseInputs'] if x['stage']==3 and x['phase']=='Initialize');worker=next(x for x in native['transitionEvents'] if x['event']=='replay-seeds-restored-before-globals-copy' and x['stage']==3);events=[json.loads(x) for x in (N/'seed-store-instruction-events.jsonl').read_bytes().splitlines()];store=next(x for x in events if x['pc']==0x456129)
assert phase['readyNs']==worker['hostMonotonicNs'] and phase['completionSource']=='original456133AfterSeedsRestoredBeforeGlobalsCopy';assert other_phase['readyNs']==store['hostMonotonicNs'] and other_phase['completionSource']=='original456129AfterScriptSeedBeforeVisualCounter_CompositeInitializationTimingNotProved' and store['hostMonotonicNs']<=worker['hostMonotonicNs']
state=(N/'selected-state.u32').read_bytes()[:26000*128];assert state==(M/'selected-state.u32').read_bytes();camera=(N/'world-camera.raw').read_bytes()[:26000*0x124];offsets=[*range(0,88,4),0x104,0x108,0x10c];assert array.array('I',(struct.unpack_from('<I',camera,n*0x124+off)[0] for n in range(26000) for off in offsets)).tobytes()==(M/'portable-camera.u32').read_bytes();assert (N/'hud-score.u32').read_bytes()[:26000*8]==(M/'portable-hud.u32').read_bytes()
spec=importlib.util.spec_from_file_location('vm_fields',R/'tools/th14-hud-completion-evidence-check-oct25.py');vm=importlib.util.module_from_spec(spec);spec.loader.exec_module(vm);fields=json.loads((M/'live-report.json').read_bytes())['fields'];diff=[];vmrows=0
for path in sorted(N.glob('live-vms-callback-*.json')):
 frame=int(path.stem.rsplit('-',1)[1]);
 if frame>26000:continue
 rows=json.loads(path.read_bytes())['rows'];actual=json.loads((M/f'portable-live-{frame}.json').read_bytes());blobs=[bytes.fromhex(row['rawVmHex']) for row in rows];handles={struct.unpack_from('<I',blob,0x570)[0]:struct.unpack_from('<I',blob,0x540)[0] for blob in blobs};assert len(handles)==len(rows)==len(actual)
 for raw,observed in zip(blobs,actual):
  expected=vm.vm_words(raw,handles);assert len(expected)==len(observed)==len(fields)==303 and expected[0]==observed[0]
  for i,(x,y) in enumerate(zip(expected,observed)):
   if x!=y:diff.append({'callback':frame,'handle':expected[0],'field':fields[i],'native':x,'portable':y})
 vmrows+=len(rows)
assert len(diff)==7 and all(x['callback'] in (22000,24000) and x['field']=='worldZ' for x in diff)
index=json.loads((N/'combat-pool-index.json').read_bytes());fields_combat=index['fields'];checkpoints=0
for entry in index['snapshots']:
 if entry['callback']>26000:continue
 compressed=(N/'combat-pools'/entry['file']).read_bytes();assert sha(compressed)==entry['sha256'];observation=json.loads(gzip.decompress(compressed));actual=json.loads((M/f"combat-{entry['callback']}.json").read_bytes());assert (observation['callback'],observation['stage'],observation['stageFrame'])==(actual['callback'],actual['stage'],actual['stageFrame'])
 for family,layout in fields_combat.items():
  expected=[]
  for row in observation['original'][family]:
   blob=bytes.fromhex(row['rawHex']);expected.append([row['slot'] if offset is None else struct.unpack_from('<H' if family=='bullets' and name=='state' else '<I',blob,offset)[0] for name,offset in layout])
  assert expected==actual['rows'][family],(entry['callback'],family)
 checkpoints+=1
publications=[json.loads(line) for line in (N/'allocation-events.jsonl').read_bytes().splitlines()];cutoff=native['anmPublicationTraceCutoffPlayerCallbacks'];portable=json.loads((M/f'portable-allocations-initial-through-{cutoff}.json').read_bytes());assert len(publications)==len(portable) and [(r['handle'],r['file'],r['script']) for r in publications]==[(r['handle'],r['file'],r['script']) for r in portable]
for name in ['selected-state.u32','portable-camera.u32','portable-hud.u32','live-report.json','combat-snapshots.json']:
 assert (M/name).read_bytes()==(OTHER/name).read_bytes(),name
for path in M.glob('combat-*.json'):
 assert path.read_bytes()==(OTHER/path.name).read_bytes(),path.name
for path in M.glob('portable-live-*.json'):
 assert path.read_bytes()==(OTHER/path.name).read_bytes(),path.name
checker=R/'tools/th14-verify-native-initialize-timing-nov03.py';positive=H/'baseline-initialize-time-verified.json';negative=H/'store-time-must-not-pass.json';assert not negative.exists()
p=subprocess.run([sys.executable,'-X','utf8',str(checker),'--native',str(N),'--model',str(M),'--output',str(positive)],capture_output=True);assert p.returncode==0,p.stderr
p=subprocess.run([sys.executable,'-X','utf8',str(checker),'--native',str(N),'--model',str(OTHER),'--output',str(negative)],capture_output=True);assert p.returncode!=0 and b'unverified Initialize timestamp' in p.stderr and not negative.exists()
result={'diagnosticDataIndependentlyChecked':True,'callbacks':26000,'originalSeedStoreSnapshotsObserved':2,'mainStageObjectNotCapturedAtEitherStore':True,'selectedStateCameraHudAndCombatEqual':True,'combatCheckpoints':checkpoints,'orderedPublications':len(publications),'vmRowsCompared':vmrows,'vmDifferingWords':len(diff),'vmDifferences':diff,'twoTimingChoicesProduceEqualCheckedPayloads':True,'originalPostStoreCompositeTimingNotProved':True,'baselineTimingGateAccepted':True,'postStoreCompositeTimingGateRejected':True,'strictAcceptance':False,'actualHistoricalOtherCaptureOrderProved':False,'productionChanged':False,'completeGame':False,'nativeEquivalent':False,'modelReportSha256':sha((M/'report.json').read_bytes()),'secondModelReportSha256':sha((OTHER/'report.json').read_bytes()),'nativeReportSha256':sha((N/'report.json').read_bytes()),'toolSha256':sha(Path(__file__).read_bytes())};(H/'independent-comparison-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
