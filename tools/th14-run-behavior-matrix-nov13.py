"""24 ordinary control cases; reuse only exact-driver completed cases."""
from pathlib import Path
import hashlib,itertools,json,os,subprocess,time
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/behavior-matrix-nov13'
driver=R/'tools/th14-run-behavior-entry-nov13.mjs';node='C:/nvm4w/nodejs/node.exe'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
build=load(H/'component/build.json');expected_driver=sha(driver);cases=list(itertools.product(range(3),range(2),range(4)))
assert not(H/'matrix-plan.json').exists()
(H/'matrix-plan.json').write_text(json.dumps(dict(pid=os.getpid(),cases=cases,total=24,
 externalHeldKeysAndPauseOnly=True,completeBombLifetimeInSixNormalCases=True,other18CasesBombActivationAnd20Frames=True,
 nativeAllModesCompared=False,hardwareVisualsAccepted=False,noRetries=True,retainInvalidV1PlayerStateFixture=True,
 driverSha256=expected_driver,buildSha256=sha(H/'component/build.json'),completeGame=False),indent=2)+'\n')
rows=[];code=0
for character,subtype,difficulty in cases:
 assert sha(driver)==expected_driver
 name=f'c{character}-s{subtype}-d{difficulty}-v2';p=H/name;reused=p.exists();started=time.monotonic()
 if not reused:
  with(H/(name+'.log')).open('xb')as f:
   q=subprocess.run([node,str(driver),str(character),str(subtype),str(difficulty)],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=230,creationflags=subprocess.CREATE_NO_WINDOW)
  code=q.returncode
 j=load(p/'report.json');platform=load(p/'platform.json')
 error=[]
 if not reused and code:error.append('driver-exit-'+str(code))
 if not(j['terminal']and j['passed']and j['closed']and j['retired']and not j['exception']and not j['errors']):error.append('declared-behavior-checkpoints')
 if j['driverSha256']!=expected_driver or j['sourceWasmSha256']!=build['outputs']['candidate']['wasmSha256']:error.append('driver-or-module-identity')
 if [j[k]for k in ['character','subtype','difficulty']]!=[character,subtype,difficulty]:error.append('selection')
 if not j['focusObserved']or j['maxActiveProjectiles']<=0 or not j['bombObserved']or(difficulty==1 and not j['bombFinished']):error.append('combat-actions')
 if platform['audibleOutput']or platform['liveDeclaredGpuFences']or platform['productionDelivery']['activeRestore']or platform['productionDelivery']['activeScene']:error.append('retirement-or-audio')
 row=dict(character=character,subtype=subtype,difficulty=difficulty,path=name,passed=not error,errors=error,reusedPreviouslyExecutedIdenticalCase=reused,frames=j['frames'],bombFinished=j['bombFinished'],reportSha256=sha(p/'report.json'),elapsedSeconds=time.monotonic()-started);rows.append(row)
 progress=dict(pid=os.getpid(),completed=len(rows),total=24,cases=rows,terminal=False,completeGame=False)
 t=H/'matrix-progress.tmp';t.write_text(json.dumps(progress,indent=2)+'\n');t.replace(H/'matrix-progress.json')
 print(json.dumps(row),flush=True)
 if error:break
result=dict(terminal=True,cases=rows,completed=len(rows),total=24,passed=len(rows)==24 and all(r['passed']for r in rows),
 actualOrdinaryInputsAndThreads=True,behavioralFunctionalChecksOnly=True,nativeAllModeReferenceComparison=False,
 fullStageCoverageAccepted=False,hardwareVisualsAccepted=False,completeGame=False,driverSha256=expected_driver)
(H/'matrix-report.json').write_text(json.dumps(result,indent=2)+'\n')
if not result['passed']:raise SystemExit(1)
