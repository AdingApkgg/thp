"""Recheck original debug-exception status and stage entries for the frozen TH14 inventory."""
from pathlib import Path
import argparse,hashlib,json,struct
R=Path(__file__).resolve().parents[1];P=R/'docs/porting/th14-mode-acceptance-inventory-nov03.json';sha=lambda b:hashlib.sha256(b).hexdigest();inventory=json.loads(P.read_bytes());assert inventory['schema']=='th14/mode-acceptance-inventory/6' and len(inventory['cases'])==30
rows=[];runs=clean=0
for case in inventory['cases']:
 entries=case['retainedNaturalRuns']+case.get('additionalObservedRuns',[]);observed=[]
 for item in entries:
  home=(R/item['path']).resolve();assert home.is_relative_to(R/'artifacts/th14');report_raw=(home/'report.json').read_bytes();assert sha(report_raw)==item['reportSha256'];report=json.loads(report_raw);data=(home/'selected-state.u32').read_bytes();assert sha(data)==item['selectedSha256'] and len(data)==item['callbacks']*128
  stages=sorted({struct.unpack_from('<I',data,i*128+120)[0] for i in range(item['callbacks'])});assert stages==item['stagesObserved']
  errors=report['debugErrors'];assert isinstance(errors,list);ok=report['childExited'] and not report['error'] and not errors;runs+=1;clean+=int(ok)
  observed.append(dict(path=item['path'],callbacks=item['callbacks'],stages=stages,debugExceptions=len(errors),exceptionGatePassed=ok,reportSha256=sha(report_raw),selectedSha256=sha(data)))
 hasclean=any(x['exceptionGatePassed'] for x in observed);allstage=any(x['exceptionGatePassed'] and set(case['expectedStages'])<=set(x['stages']) for x in observed)
 rows.append(dict(key=case['key'],expectedStages=case['expectedStages'],retainedRuns=observed,hasExceptionFreeRun=hasclean,allStageEntriesInOneExceptionFreeRun=allstage,wholeModeEquivalent=False))
assert runs==46 and clean==45 and sum(x['hasExceptionFreeRun'] for x in rows)==30 and sum(x['allStageEntriesInOneExceptionFreeRun'] for x in rows)==28
assert [x['key'] for x in rows if not x['allStageEntriesInOneExceptionFreeRun']]==['marisaa-normal','marisaa-hard']
r=next(x for x in rows if x['key']=='reimub-easy');assert sorted(x['debugExceptions'] for x in r['retainedRuns'])==[0,12]
original=next(x for x in inventory['cases'] if x['key']=='reimub-easy');clean_run=next(x for x in original['retainedNaturalRuns'] if x['path'].endswith('camera-phases-hardware-oct25'));assert not clean_run['selected32ComparisonReports'] and clean_run['preferredComparisonPath'] is None
result=dict(verifiedInventoryExceptionAudit=True,inventorySha256=sha(P.read_bytes()),modePairs=30,retainedRuns=runs,exceptionFreeRuns=clean,pairsWithExceptionFreeRun=30,pairsWithAllStageEntriesInOneExceptionFreeRun=28,pairsWithoutAllStageEntriesInExceptionFreeRun=['marisaa-normal','marisaa-hard'],reimubEasyCleanRunHasFullComparisonProof=False,runEntryCoverageDoesNotProveFullGameplayOrSourceEof=True,completeGame=False,nativeEquivalent=False,rows=rows,verifierSha256=sha(Path(__file__).read_bytes()))
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path,default=R/'docs/porting/th14-mode-debug-exception-audit-nov03.json');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'docs/porting') or out.is_relative_to(R/'artifacts/th14');data=(json.dumps(result,indent=2)+'\n').encode()
if a.check:assert out.read_bytes()==data
else:out.write_bytes(data)
print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
