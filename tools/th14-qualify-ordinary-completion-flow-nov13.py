"""Qualify completion-boundary, ending and fresh-save-read handoffs."""
from pathlib import Path
import ast,hashlib,importlib.util,json,struct
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/ordinary-completion-flow-nov13'
load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
build=load(H/'component-v2/build.json')
for n,h in {**build['sourceBindingsByMode']['candidate'],**build['objectBindings']}.items():assert sha(R/n)==h,n
reports={m:load(H/(m+'-v2')/'report.json')for m in ['write','read']}
for mode,j in reports.items():
 assert j['passed']and j['retired']and j['closed']and not j['errors']and j['exception']is None
 assert j['sourceWasmSha256']==sha(H/'component-v2/candidate.wasm')==build['outputs']['candidate']['wasmSha256']
 assert j['driverSha256']==sha(H/(mode+'-v2')/'executed-driver.mjs')
 assert all(w['closed']and w['exitCode']==0 for w in j['physicalWorkers'])
 p=load(H/(mode+'-v2')/'platform.json');assert not p['audibleOutput']and not p['pendingTimers']and not any(p['liveObjects'].values())
 clock=load(H/(mode+'-v2')/'process-clock.json');assert not clock['active']and clock['beginCalls']==clock['endCalls']==1
calls=load(H/'write-v2/boundary-calls.json');assert [x['stage']for x in calls]==[1,2,3,4,5,6]
for x in calls:assert x['before'][:3]==[1,x['stage'],0]
ending=load(H/'write-v2/ending-entered.json')['flow'];assert ending[0]==5 and ending[3]==2 and ending[7:11]==[1,1,1,17]
result=load(H/'write-v2/result-and-flush.json')['flow'];fresh=load(H/'read-v2/fresh-title-read.json')['flow']
assert result[5]==14 and fresh[5]==1
for s in [result,fresh]:assert s[7:12]==[1,1,1,17,1]and s[12:18]==[0,1,0,0,0,0]
# Independent container decoder, followed by full record-format checks.
source=R/'tools/th14-audit-root-full-extra-nov08.py';tree=ast.parse(source.read_text());function=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='decode_score')
spec=importlib.util.spec_from_file_location('completion_score_codec',R/'tools/th-replay-container.py');mirror=importlib.util.module_from_spec(spec);spec.loader.exec_module(mirror)
scope=dict(struct=struct,mirror=mirror);exec(compile(ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[])),str(source),'exec'),scope)
score=H/'write-v2/save/scoreth14.dat';encoded=score.read_bytes();decoded=scope['decode_score'](encoded);assert len(decoded)==149076
assert (H/'read-v2/save/scoreth14.dat').read_bytes()==encoded
for i in range(8):
 start=i*0x5298;n=0x5298 if i<7 else 0x42c;record=decoded[start:start+n]
 assert struct.unpack_from('<I',record,0)[0]==(0x15243 if i<7 else 0x15453)
 assert struct.unpack_from('<I',record,8)[0]==n and sum(record[8:])==struct.unpack_from('<I',record,4)[0]
 if i<7:assert struct.unpack_from('<I',record,12)[0]==i
assert struct.unpack_from('<I',decoded,0x5298+0x7c4)[0]==1
assert struct.unpack_from('<I',decoded,0x5298+0x7e0)[0]==1
assert [decoded[7*0x5298+offset]for offset in [0x16,0x18]]==[1,17]
(H/'observed-decoded.bin').write_bytes(decoded)
j=dict(passed=True,actualApplicationProcesses=2,actualCppThreads=True,completionMethodCalls=6,
 actualEndingStaffAndResultRoute=True,freshApplicationTitleRead=True,onlyReimuBExtraAvailable=True,
 encodedScoreBytes=len(encoded),decodedScoreBytes=len(decoded),recordChecksumsVerified=8,
 completionCountersAndEndingFlagsPreserved=True,allMeasuredResourcesRetired=True,silent=True,
 completionBoundaryInvokedDirectly=True,naturalFullCampaignAccepted=False,naturalUnlockProgressionAccepted=False,
 actualGpuAccepted=False,browserPersistenceAccepted=False,fullGameAccepted=False,
 retainedFailure='write-v1 triggered completion before the new battle/resources were active; retired cleanly',
 reportHashes={m:sha(H/(m+'-v2')/'report.json')for m in reports},scoreSha256=sha(score),
 nativeCodecPassed=load(H/'native-codec-qualified.json')['passed']if(H/'native-codec-qualified.json').exists()else False)
(H/'qualified.json').write_text(json.dumps(j,indent=2)+'\n');print(json.dumps(j,indent=2))
