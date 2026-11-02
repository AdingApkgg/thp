"""Require original Initialize events for every active later TH14 stage, then run v2."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,sys,tempfile
R=Path(__file__).resolve().parents[1];sha=lambda b:hashlib.sha256(b).hexdigest()
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--model',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();n=a.native.resolve();m=a.model.resolve();out=a.output.resolve();assert n.is_relative_to(R/'artifacts/th14') and m.is_relative_to(R/'artifacts/th14') and out.is_relative_to(R/'artifacts/th14') and not out.exists()
report_raw=(n/'report.json').read_bytes();report=json.loads(report_raw);model_raw=(m/'report.json').read_bytes();model=json.loads(model_raw);selected=(n/'selected-state.u32').read_bytes();count=model['callbacks'];assert count>0 and len(selected)==report['callbacks']*128 and len(selected)>=count*128 and sha(selected)==report['selectedSha256']
first=struct.unpack_from('<I',selected,120)[0];assert 1<=first<=7;active=set();last=first
for i in range(count):
 stage=struct.unpack_from('<I',selected,i*128+120)[0];frame=struct.unpack_from('<I',selected,i*128)[0];assert 1<=stage<=7
 assert stage>=last,'Unsupported stage reentry or backward transition';last=stage
 if stage!=first and frame>0:active.add(stage)
events=[json.loads(x) for x in (n/'transition-events.jsonl').read_bytes().splitlines()] if (n/'transition-events.jsonl').exists() else []
observed={e['stage'] for e in events if e.get('event')=='replay-seeds-restored-before-globals-copy'}
missing=active-observed;assert not missing, 'No original Initialize event for active later stage(s): '+','.join(map(str,sorted(missing)))
assert active<={x['stage'] for x in model['observedPhaseInputs'] if x['phase']=='Initialize'},'No model Initialize input for an active later stage'
with tempfile.TemporaryDirectory(prefix='init-v3-',dir=out.parent) as tmp:
 prior=Path(tmp)/'v2.json';subprocess.run([sys.executable,'-X','utf8',str(R/'tools/th14-verify-native-initialize-timing-v2-nov03.py'),'--native',str(n),'--model',str(m),'--output',str(prior)],cwd=R,check=True,capture_output=True);proof=json.loads(prior.read_bytes())
result=dict(passed=True,scope='Requires an original Initialize event and model input for every later stage with a positive observed stage frame, then runs the existing timing binding. An entered stage that never reaches a positive frame is not covered by this requirement.',firstObservedStage=first,activeLaterStages=sorted(active),observedInitializeStages=sorted(observed),reportedInputCoverageComplete=True,priorVerifierSha256=proof['verifierSha256'],nativeReportSha256=sha(report_raw),nativeSelectedSha256=sha(selected),modelReportSha256=sha(model_raw),completeGame=False,nativeEquivalent=False,verifierSha256=sha(Path(__file__).read_bytes()))
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
