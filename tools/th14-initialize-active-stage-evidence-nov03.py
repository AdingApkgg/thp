"""Reproduce active-stage Initialize timing coverage, including omitted-event control."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,sys,tempfile
R=Path(__file__).resolve().parents[1];D=R/'artifacts/th14/frame-rng-scope-nov02/counter-regressions';W=R/'artifacts/th14/initialize-active-wrapper-v2-nov03';v2=R/'tools/th14-verify-native-initialize-timing-v2-nov03.py';v3=R/'tools/th14-verify-native-initialize-timing-v3-nov03.py';sha=lambda b:hashlib.sha256(b).hexdigest();bindings={}
def raw(p):
 p=p.resolve();assert p.is_relative_to(R);b=p.read_bytes();bindings[p.relative_to(R).as_posix()]={'bytes':len(b),'sha256':sha(b)};return b
def load(p):return json.loads(raw(p))
for path in [v2,v3,R/'tools/th14-verify-native-debug-exceptions-nov03.py',R/'tools/th14-verify-native-campaign-exceptions-timing-v3-nov03.py']:raw(path)
summary=load(D/'summary.json');assert summary['cases']==16 and summary['passed'];rows=[]
with tempfile.TemporaryDirectory(prefix='active-stage-test-',dir=R/'artifacts/th14') as temp:
 T=Path(temp)
 def run(script,n,m,out):return subprocess.run([sys.executable,'-X','utf8',str(script),'--native',str(n),'--model',str(m),'--output',str(out)],capture_output=True,cwd=R)
 for i in range(16):
  case=load(D/f'case-{i}/plan.json')['cases'][0];n=R/case['native'];m=D/f'case-{i}'/case['key']/'model';report=load(n/'report.json');model=load(m/'report.json');test=run(v3,n,m,T/f'case-{i}.json');assert test.returncode==0,test.stderr;proof=json.loads((T/f'case-{i}.json').read_bytes());assert proof['nativeReportSha256']==sha((n/'report.json').read_bytes()) and proof['modelReportSha256']==sha((m/'report.json').read_bytes())
  rows.append(dict(key=case['key'],callbacks=model['callbacks'],firstObservedStage=proof['firstObservedStage'],activeLaterStages=proof['activeLaterStages'],originalReportSha256=proof['nativeReportSha256'],modelReportSha256=proof['modelReportSha256'],debugExceptions=len(report['debugErrors']),timingGatePassed=True))
 assert sum(bool(x['debugExceptions']) for x in rows)==1
 n=T/'native';m=T/'model';n.mkdir();m.mkdir();data=bytearray(256);struct.pack_into('<I',data,0,1);struct.pack_into('<I',data,120,1);struct.pack_into('<I',data,128,1);struct.pack_into('<I',data,248,2);(n/'selected-state.u32').write_bytes(data);report=dict(callbacks=2,selectedSha256=sha(data),transitionEvents=[],hardwareBreakpointsOnly=True,rngOrCounterWrites=0,instructionBytesPatched=0);model=dict(callbacks=2,schedulerPhases='observed',completed=True,completeGame=False,nativeEquivalent=False,observedPhaseInputs=[]);(n/'report.json').write_text(json.dumps(report));(m/'report.json').write_text(json.dumps(model))
 old=run(v2,n,m,T/'old.json');new=run(v3,n,m,T/'new.json');assert old.returncode==0 and new.returncode!=0 and not (T/'new.json').exists() and b'No original Initialize event' in new.stderr
 struct.pack_into('<I',data,120,7);struct.pack_into('<I',data,248,7);(n/'selected-state.u32').write_bytes(data);report['selectedSha256']=sha(data);(n/'report.json').write_text(json.dumps(report));extra=run(v3,n,m,T/'extra.json');assert extra.returncode==0,extra.stderr
 struct.pack_into('<I',data,120,2);struct.pack_into('<I',data,248,1);(n/'selected-state.u32').write_bytes(data);report['selectedSha256']=sha(data);(n/'report.json').write_text(json.dumps(report));reentry=run(v3,n,m,T/'reentry.json');assert reentry.returncode!=0 and b'Unsupported stage reentry' in reentry.stderr and not (T/'reentry.json').exists()
positive=load(W/'positive-exceptions.json');timing=load(W/'positive-timing.json');strict=load(W/'positive-raw.json');assert positive['passed'] and timing['passed'] and timing['verifierSha256']==sha(v3.read_bytes()) and strict['verifiedFiniteEvidence'] and strict['callbacks']==66909
assert b'Original capture contains debug exceptions' in raw(W/'negative.log') and not any((W/('negative-'+x+'.json')).exists() for x in ['exceptions','timing','raw'])
result=dict(verifiedActiveStageCoverage=True,coreCommit='22c4f853fc1cb81b8a0c0891b88023f2f5dc065e',existingTimingCases=16,existingTimingCasesPassed=16,exceptionGateNotAppliedToSixteenTimingUnit=True,existingCasesWithDebugExceptions=1,missingStageEventAndInputAcceptedByV2=True,missingStageEventAndInputRejectedByV3=True,initialExtraOnlyAccepted=True,backwardTransitionRejected=True,combinedCleanCaseCallbacks=66909,combinedExceptionCaseRejectedBeforeOutputs=True,positiveFrameOnlyCoverage=True,completeGame=False,nativeEquivalent=False,rows=rows,bindings=bindings,verifierSha256=sha(Path(__file__).read_bytes()))
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path,default=R/'docs/porting/th14-initialize-active-stage-nov03.json');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'docs/porting') or out.is_relative_to(R/'artifacts/th14');data=(json.dumps(result,indent=2)+'\n').encode()
if a.check:assert out.read_bytes()==data
else:out.write_bytes(data)
print(json.dumps({k:v for k,v in result.items() if k not in ('rows','bindings')}))
