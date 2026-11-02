"""Reproduce Scene timing gate and retain the six-stage camera counterfactual as diagnostic."""
from pathlib import Path
import argparse,copy,hashlib,json,subprocess,sys,tempfile
R=Path(__file__).resolve().parents[1];D=R/'artifacts/th14/frame-rng-scope-nov02/counter-regressions';H=R/'artifacts/th14/replay-candidates-second-nov03/case-marisaa-normal';W=R/'artifacts/th14/scene-gate-wrapper-nov03';gate=R/'tools/th14-verify-native-scene-boundaries-nov03.py';sha=lambda b:hashlib.sha256(b).hexdigest();bindings={}
def raw(p):
 p=p.resolve();assert p.is_relative_to(R);b=p.read_bytes();bindings[p.relative_to(R).as_posix()]={'bytes':len(b),'sha256':sha(b)};return b
def load(p):return json.loads(raw(p))
for p in [gate,R/'tools/th14-verify-native-campaign-exceptions-timing-v4-nov03.py',R/'tools/th14-compare-native-campaign-retained-camera-nov01.mjs',R/'tools/th14-compare-native-extra-campaign-nov01.mjs',R/'tools/th14-normal-stage2-after-hypothesis-nov03.mjs']:raw(p)
summary=load(D/'summary.json');assert summary['cases']==16 and summary['passed'];rows=[]
with tempfile.TemporaryDirectory(prefix='scene-gate-',dir=H) as tmp:
 T=Path(tmp)
 def run(n,m,out):return subprocess.run([sys.executable,'-X','utf8',str(gate),'--native',str(n),'--model',str(m),'--output',str(out)],cwd=R,capture_output=True)
 for i in range(16):
  c=load(D/f'case-{i}/plan.json')['cases'][0];n=R/c['native'];m=D/f'case-{i}'/c['key']/'model';native=load(n/'report.json');model=load(m/'report.json');p=run(n,m,T/f'case-{i}.json');assert p.returncode==0,p.stderr;proof=json.loads((T/f'case-{i}.json').read_bytes());assert proof['nativeReportSha256']==sha(raw(n/'report.json')) and proof['modelReportSha256']==sha(raw(m/'report.json'))
  rows.append(dict(key=c['key'],callbacks=model['callbacks'],sceneInputs=proof['sceneInputs'],activeLaterStages=proof['activeLaterStages'],debugExceptions=len(native['debugErrors']),sceneTimeGatePassed=True))
 assert sum(bool(x['debugExceptions']) for x in rows)==1
 native=H/'native';baseline=H/'model';hypothesis=H/'model-stage2-after-hypothesis';assert run(native,baseline,T/'baseline.json').returncode==0 and run(native,hypothesis,T/'hypothesis.json').returncode!=0 and not(T/'hypothesis.json').exists()
 model=load(baseline/'report.json');synthetic=T/'model';synthetic.mkdir()
 for kind in ['wrong-time','missing-stage','wrong-source','unreviewed-driver']:
  r=copy.deepcopy(model);scene=[x for x in r['observedPhaseInputs'] if x['phase']=='Scene']
  if kind=='wrong-time':scene[0]['readyNs']+=1
  if kind=='missing-stage':r['observedPhaseInputs'].remove(scene[0])
  if kind=='wrong-source':scene[0]['completionSource']='original40d447AfterSceneCameraCopy'
  if kind=='unreviewed-driver':r['comparisonToolSha256']='0'*64
  (synthetic/'report.json').write_text(json.dumps(r));assert run(native,synthetic,T/(kind+'.json')).returncode!=0 and not(T/(kind+'.json')).exists()
 events=[json.loads(x) for x in raw(native/'scene-camera-copy-events.jsonl').splitlines()];before=next(e for e in events if e['stage']==2 and e['event']=='scene-camera-copy-before');after=next(e for e in events if e['stage']==2 and e['event']=='scene-camera-copy-after');assert before['readOnly'] and after['readOnly'] and before['threadId']==after['threadId'] and before['hostMonotonicNs']<after['hostMonotonicNs'] and before['sourceRightHex']=='000000000000000000000000' and after['copiedRightHex']=='000080bf0000000000000000'
 h=load(hypothesis/'report.json');v=next(x for x in h['observedPhaseInputs'] if x['stage']==2 and x['phase']=='Scene');assert v['completionSource']=='counterfactualStage2AfterDrawNotObservedPerWord' and v['readyNs']==after['hostMonotonicNs'];proof=load(H/'stage2-after-hypothesis-raw-verified.json');assert proof['verifiedFiniteEvidence'] and proof['callbacks']==107388 and proof['allSelected32Equal'] and proof['allCamera25Equal'] and proof['allHud2Equal'] and proof['allVm303AndRegistryOrderEqual'] and proof['allCapturedCombatWordsEqual'] and proof['vm303Rows']==2538 and proof['combatCheckpoints']==1055 and proof['orderedPublications']==2698
 for name,b in proof['bindings'].items():assert sha((R/name).read_bytes())==b['sha256'],name
positive=load(W/'positive-scene.json');strict=load(W/'positive-raw.json');assert positive['passed'] and strict['verifiedFiniteEvidence'] and strict['callbacks']==66909 and not(W/'negative-scene.json').exists() and not(W/'negative-raw.json').exists() and b'Unreviewed Scene scheduler driver' in raw(W/'negative.log')
result=dict(verifiedSceneBoundaryGate=True,existingTimingCases=16,existingSceneTimingCasesPassed=16,exceptionGateNotAppliedToSixteenTimingUnit=True,existingCasesWithDebugExceptions=1,counterfactualRawPayloadEqual=True,counterfactualRejectedBySceneGate=True,counterfactualVmRows=2538,counterfactualCombatCheckpoints=1055,counterfactualInitialPublications=2698,syntheticTamperControlsRejected=4,combinedCleanCaseCallbacks=66909,combinedCounterfactualRejectedBeforeRawProof=True,exactNativeCopyWordOrderingProved=False,wholeModeEquivalent=False,completeGame=False,nativeEquivalent=False,rows=rows,bindings=bindings,verifierSha256=sha(Path(__file__).read_bytes()))
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path,default=R/'docs/porting/th14-scene-boundary-gate-nov03.json');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'docs/porting') or out.is_relative_to(H);data=(json.dumps(result,indent=2)+'\n').encode()
if a.check:assert out.read_bytes()==data
else:out.write_bytes(data)
print(json.dumps({k:v for k,v in result.items() if k not in ('rows','bindings')}))
