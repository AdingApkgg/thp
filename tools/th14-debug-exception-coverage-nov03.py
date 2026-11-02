"""Audit debug-exception coverage for sixteen retained TH14 regression captures."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,tempfile
R=Path(__file__).resolve().parents[1];C=R/'artifacts/th14/frame-rng-scope-nov02/counter-regressions';H=R/'artifacts/th14/replay-alternatives-nov03/case-marisaa-hard-seed-probe';gate=R/'tools/th14-verify-native-debug-exceptions-nov03.py';sha=lambda b:hashlib.sha256(b).hexdigest();bindings={}
def raw(p):
 p=p.resolve();assert p.is_relative_to(R);v=p.read_bytes();bindings[p.relative_to(R).as_posix()]={'bytes':len(v),'sha256':sha(v)};return v
def load(p):return json.loads(raw(p))
summary=load(C/'summary.json');assert summary['passed'] and summary['cases']==16 and summary['callbacks']==1579705 and all(x['strictPassed'] and x['independentVerifierExitCode']==0 for x in summary['results'])
raw(gate);raw(R/'tools/th14-verify-native-campaign-exceptions-timing-nov03.py');rows=[]
with tempfile.TemporaryDirectory(prefix='debug-gate-',dir=H) as tmp:
 t=Path(tmp)
 def run(native,index):
  out=t/f'proof-{index}.json';p=subprocess.run([sys.executable,'-X','utf8',str(gate),'--native',str(native),'--output',str(out)],capture_output=True);return p.returncode,out.exists()
 for i in range(16):
  case=load(C/f'case-{i}/plan.json')['cases'][0];native=R/case['native'];report=load(native/'report.json');errors=report['debugErrors'];assert isinstance(errors,list)
  code,wrote=run(native,i);assert (code==0 and wrote)==(len(errors)==0)
  rows.append(dict(key=case['key'],callbacks=report['callbacks'],debugExceptions=len(errors),exceptionGatePassed=(code==0),originalPayloadComparisonsPassed=True,reportSha256=sha((native/'report.json').read_bytes())))
 assert len([x for x in rows if x['exceptionGatePassed']])==15
 excluded=[x for x in rows if not x['exceptionGatePassed']];assert len(excluded)==1 and excluded[0]['key']=='reimub-easy' and excluded[0]['debugExceptions']==12
 excluded_case=load(C/'case-9/plan.json')['cases'][0];assert excluded_case['key']=='reimub-easy' and all(x['firstChance']==1 for x in load(R/excluded_case['native']/'report.json')['debugErrors'])
 probe=load(H/'native/report.json');end=load(H/'follower-v4-end.json');assert len(probe['debugErrors'])==10 and all(x['firstChance']==1 for x in probe['debugErrors']) and end['strictAcceptanceProhibited'] and not end['originalObservationValidated'] and len(end['comparisons'])==2 and all(x['independentVerifierExitCode']==0 for x in end['comparisons'])
 assert run(H/'native',30)==(1,False)
 controls=[{'childExited':True,'error':''},{'childExited':True,'error':'','debugErrors':None},{'childExited':True,'error':'unexpected','debugErrors':[]},{'childExited':False,'error':'','debugErrors':[]}]
 for i,c in enumerate(controls):
  d=t/f'control-{i}';d.mkdir();(d/'report.json').write_text(json.dumps(c));assert run(d,40+i)==(1,False)
wrapper=R/'artifacts/th14/exception-gate-wrapper-nov03';positive=load(wrapper/'positive-exceptions.json');timing=load(wrapper/'positive-timing.json');strict=load(wrapper/'positive-raw.json')
assert positive['passed'] and positive['debugExceptionCount']==0 and timing['passed'] and strict['verifiedFiniteEvidence'] and strict['callbacks']==66909
assert b'Original capture contains debug exceptions' in raw(wrapper/'negative.log') and not any((wrapper/('negative-'+name+'.json')).exists() for name in ['exceptions','timing','raw'])
result=dict(verifiedExceptionGate=True,coreCommit='22c4f853fc1cb81b8a0c0891b88023f2f5dc065e',priorRegressionCases=16,priorSelectedPayloadAndRawComparisonsPassed=16,priorCasesPassingNewExceptionGate=15,priorCaseExcludedByNewGate=excluded[0]['key'],priorExcludedFirstChanceExceptions=excluded[0]['debugExceptions'],newProbeCallbacks=32000,newProbeFirstChanceExceptions=10,newProbeRawPayloadComparisonsPassed=2,newProbeStrictAcceptance=False,missingOrMalformedAndFailedChildControlsRejected=4,exceptionBearingRealReportsRejected=2,exceptionCausesEstablished=False,combinedWrapperCleanCasePassed=True,combinedWrapperExceptionCaseRejectedBeforeOutputs=True,priorResultNotRewritten=True,completeGame=False,nativeEquivalent=False,rows=rows,bindings=bindings,verifierSha256=sha(Path(__file__).read_bytes()))
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path,default=R/'docs/porting/th14-debug-exception-coverage-nov03.json');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'docs/porting') or out.is_relative_to(H);data=(json.dumps(result,indent=2)+'\n').encode()
if a.check:assert out.read_bytes()==data
else:out.write_bytes(data)
print(json.dumps({k:v for k,v in result.items() if k not in ('rows','bindings')}))
