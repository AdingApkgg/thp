"""Summarize current-core mode receipts under all four v4 acceptance gates."""
from pathlib import Path
import argparse,collections,hashlib,json,struct
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/replay-candidates-second-nov03/current-mode-v4-audit';base=R/'artifacts/th14/frame-rng-scope-nov02/counter-regressions';sha=lambda b:hashlib.sha256(b).hexdigest();end_raw=(H/'end.json').read_bytes();end=json.loads(end_raw);assert end['casesCompleted']==16 and end['v4Passes']==15 and not end['newOriginalProcessesLaunched'];wasm=end['sourceWasmSha256'];assert wasm=='f00a33cb9687fb544441d71bf9e5d78249b4d2e00d4059d59e7736ab1fb1c6eb'
gates={'exceptions':'th14-verify-native-debug-exceptions-nov03.py','initialize':'th14-verify-native-initialize-timing-v3-nov03.py','scene':'th14-verify-native-scene-boundaries-nov03.py','raw':'th14-verify-native-campaign.py'};rows=[];unique=set();complete_entries=set();reimub=None
for row in end['cases']:
 i=row['index'];old=base/f'case-{i}';plan_raw=(old/'plan.json').read_bytes();assert sha(plan_raw)==row['planSha256'];case=json.loads(plan_raw)['cases'][0];assert case['key']==row['key'] and case['selection']==row['selection'];n=R/case['native'];m=old/case['key']/'model';assert sha((n/'report.json').read_bytes())==row['nativeReportSha256'] and sha((m/'report.json').read_bytes())==row['modelReportSha256'];report=json.loads((n/'report.json').read_bytes());assert report['callbacks']==row['callbacks'] and len(report['debugErrors'])==row['debugExceptions']
 selected=(n/'selected-state.u32').read_bytes();assert len(selected)==report['callbacks']*128 and sha(selected)==report['selectedSha256'];stages=sorted({struct.unpack_from('<I',selected,j+120)[0]for j in range(0,len(selected),128)});expected=[7] if row['selection'][2]==4 else list(range(1,7));covered=set(expected)<=set(stages);pair=tuple(row['selection'][:3]);receipt_hashes={};raw=None
 if row['strictV4Passed']:
  assert row['exitCode']==0 and not report['debugErrors'] and row['passedGateReceipts']==list(gates)
  for gate,script in gates.items():
   data=(H/f'case-{i}'/(gate+'.json')).read_bytes();proof=json.loads(data);assert proof['verifierSha256']==sha((R/'tools'/script).read_bytes());receipt_hashes[gate]=sha(data)
   if gate!='raw':assert proof['passed'] and proof['nativeReportSha256']==row['nativeReportSha256']
   if gate in ('initialize','scene'):assert proof['modelReportSha256']==row['modelReportSha256']
   if gate=='raw':
    raw=proof;assert raw['verifiedFiniteEvidence'] and raw['wasmSha256']==wasm and raw['callbacks']==row['callbacks'] and raw['selection']==row['selection'] and raw['stagesObserved']==stages and all(raw[k]for k in ['allSelected32Equal','allCamera25Equal','allHud2Equal','allVm303AndRegistryOrderEqual','allCapturedCombatWordsEqual'])
  unique.add(pair)
  if covered:complete_entries.add(pair)
 else:
  assert row['key']=='reimub-easy' and row['debugExceptions']==12 and row['exitCode']!=0 and not row['passedGateReceipts'];assert all(x['code']==0xe06d7363 and x['firstChance']for x in report['debugErrors'])
 result=dict(key=row['key'],selection=row['selection'],callbacks=row['callbacks'],stagesObserved=stages,allTargetStageEntriesObserved=covered,strictV4Passed=row['strictV4Passed'],reportedDebugExceptions=row['debugExceptions'],nativeReportSha256=row['nativeReportSha256'],modelReportSha256=row['modelReportSha256'],gateReceiptSha256=receipt_hashes)
 if raw:result.update(vm303Rows=raw['vm303Rows'],combatCheckpoints=raw['combatCheckpoints'],orderedPublications=raw['orderedPublications'])
 if row['key']=='reimub-easy':result['firstChanceExceptionCallbacks']=dict(sorted(collections.Counter(str(x['callbacks'])for x in report['debugErrors']).items()))
 if row['key']=='reimub-full':reimub=result
 rows.append(result)
assert reimub and reimub['strictV4Passed'] and reimub['callbacks']==122537
result=dict(verifiedCurrentCoreModeGateAudit=True,cases=rows,casesAudited=16,strictV4Passes=15,rawComparisonHistoryNotOverwritten=True,distinctModePairsWithV4Pass=len(unique),distinctModePairsWithV4PassAndAllTargetEntries=len(complete_entries),totalCapturedCallbacks=sum(x['callbacks']for x in rows),passedCapturedCallbacks=sum(x['callbacks']for x in rows if x['strictV4Passed']),reimubNormalCurrentRecordPassed=True,old36826RngDifferenceClosed=False,originalFullGuiAndWholeFrameAndAudioAccepted=False,wholeModeEquivalent=False,completeGame=False,nativeEquivalent=False,sourceWasmSha256=wasm,auditEndSha256=sha(end_raw),verifierSha256=sha(Path(__file__).read_bytes()),scope='Current v4 exception, Initialize timing, Scene timing and independently recomputed raw payload gates applied to 16 retained current-core comparisons. Runs can cover the same mode more than once or end before all target stages. This does not prove source Replay EOF, ordinary GUI, independent scheduling, all pixels/audio or whole-game equivalence; previous raw-only passes retain their original scope.')
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path,default=R/'docs/porting/th14-current-mode-v4-nov03.json');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'docs/porting') or out.is_relative_to(R/'artifacts/th14');data=(json.dumps(result,indent=2)+'\n').encode()
if a.check:assert out.read_bytes()==data
else:assert not out.exists();out.write_bytes(data)
print(json.dumps({k:v for k,v in result.items()if k!='cases'}))
