"""Extend only the TH14 Marisa A Normal stage-entry inventory after terminal proof."""
from pathlib import Path
import argparse,copy,hashlib,json,subprocess
R=Path(__file__).resolve().parents[1];BASE='7cb561b8a3a9ef1d4be2d4f141935e369240c81b';NAME='docs/porting/th14-mode-acceptance-inventory-nov03.json';BASE_SHA='db5b7fe6fd3d2489b9bc88652ce905162078a09614b507c19286f97a199d23c4';sha=lambda b:hashlib.sha256(b).hexdigest()
def expected():
 original=subprocess.check_output(['git','-C',str(R/'tools/tmp/github-source-release'),'show',BASE+':'+NAME]);assert sha(original)==BASE_SHA;base=json.loads(original);assert base['pairsWithNaturalNativeRun']==30 and base['pairsWithAllStageEntriesObserved']==28
 proof=json.loads((R/'docs/porting/th14-marisaa-normal-six-stage-nov03.json').read_bytes());assert proof['verifiedFiniteMarisaANormalSixStageEntries'] and proof['observedStages']==[1,2,3,4,5,6] and proof['debugExceptions']==0 and not proof['sourceReplayEofProved']
 result=copy.deepcopy(base);row=next(x for x in result['cases'] if x['key']=='marisaa-normal');assert (row['character'],row['subtype'],row['difficulty'])==(1,0,1) and not row['allStageEntriesObserved'] and not row['wholeModeEquivalent']
 h=R/'artifacts/th14/replay-candidates-second-nov03/case-marisaa-normal';n=h/'native';m=h/'model';rel=lambda p:p.relative_to(R).as_posix();digest=lambda p:sha(p.read_bytes());native=json.loads((n/'report.json').read_bytes());end=json.loads((h/'queue-end.json').read_bytes())
 comparison={'strictAndIndependentPassed':proof['strictAndIndependentPassed'],'modelComparisonPassed':end['modelComparisonPassed'],'modelExitCode':end['modelExitCode'],'independentVerifierExitCode':end['independentVerifierExitCode']}
 if (m/'report.json').exists():comparison.update(path=rel(m/'report.json'),reportSha256=digest(m/'report.json'))
 if proof['strictAndIndependentPassed']:
  for key,file in [('exceptionProof','exception-verified.json'),('timingProof','timing-verified.json'),('rawProof','raw-verified.json')]:comparison[key+'Path']=rel(h/file);comparison[key+'Sha256']=digest(h/file)
  comparison.update(allRetainedSelectedCameraHudVmCombatAndInitialPublicationsExact=True,**proof['strictCounts'])
 else:comparison['allRetainedSelectedCameraHudVmCombatAndInitialPublicationsExact']=False
 row.setdefault('additionalObservedRuns',[]).append({'path':rel(n),'reportSha256':digest(n/'report.json'),'initialSnapshotSha256':digest(n/'untouched-first-player.json'),'selectedSha256':digest(n/'selected-state.u32'),'callbacks':proof['callbacks'],'stagesObserved':proof['observedStages'],'forcedReplayEndMenuObserved':True,'sourceReplayEofProved':False,'clearCompletionNotAsserted':True,'intactOriginalReplayDeclared':True,'instructionBytesPatched':0,'rngOrCounterWrites':0,'debugExceptions':0,'replaySha256':native['sourceFullReplaySha256'],'comparison':comparison,'actualNativeMusicAndEffectsMasterLevelsZero':True,'sourceCoreCommit':proof['coreCommit'],'publicEvidence':'docs/porting/th14-marisaa-normal-six-stage-nov03.json'})
 row['allStageEntriesObserved']=True;result.update(schema='th14/mode-acceptance-inventory/7',date='2026-11-03',pairsWithAllStageEntriesObserved=29,toolSha256=sha(Path(__file__).read_bytes()))
 assert len(result['cases'])==result['modePairs']==result['pairsWithNaturalNativeRun']==30 and sum(x['allStageEntriesObserved'] for x in result['cases'])==29 and [x for x in result['cases'] if x['key']!='marisaa-normal']==[x for x in base['cases'] if x['key']!='marisaa-normal']
 files=[n/'report.json',n/'untouched-first-player.json',n/'selected-state.u32',h/'native-silence-verified.json',R/'docs/porting/th14-marisaa-normal-six-stage-nov03.json']
 if (m/'report.json').exists():files.append(m/'report.json')
 if proof['strictAndIndependentPassed']:files.extend(h/x for x in ['exception-verified.json','timing-verified.json','raw-verified.json'])
 for p in files:result['reportBindings'][rel(p)]=digest(p)
 result.setdefault('additionalExtensions',[]).append({'baseSourceCommit':BASE,'baseInventorySha256':BASE_SHA,'updatedModeOnly':'marisaa-normal','otherTwentyNineModesFrozenUnchanged':True,'newObservedStages':[1,2,3,4,5,6],'sourceReplayEofProved':False,'fullCapturedRunCompared':bool((m/'report.json').exists()),'allRetainedFieldsIndependentlyExact':proof['strictAndIndependentPassed'],'sourceCoreCommit':proof['coreCommit'],'wholeModeEquivalent':False,'completeGame':False})
 assert not result['completeGame'] and not result['nativeEquivalent'];return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();result=expected();out=R/'docs/porting/th14-mode-acceptance-inventory-v7-nov03.json';data=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode()
 if a.check:assert out.read_bytes()==data
 else:out.write_bytes(data)
 print(json.dumps({'verifiedSingleModeInventoryExtension':True,'pairsWithNaturalNativeRun':30,'pairsWithAllStageEntriesObserved':29,'otherTwentyNineModesFrozenUnchanged':True,'sourceReplayEofProved':False,'completeGame':False}))
