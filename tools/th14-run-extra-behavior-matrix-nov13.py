from pathlib import Path
import hashlib,itertools,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/behavior-matrix-nov13'
driver=R/'tools/th14-run-extra-behavior-entry-nov13.mjs';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
assert load(H/'matrix-report.json')['passed'];expected=sha(driver);rows=[]
plan=H/'extra-matrix-plan.json';assert not plan.exists();plan.write_text(json.dumps(dict(pid=os.getpid(),cases=6,externalUnlockedSave=True,noUserSaveChanges=True,unlockEarnedThroughPlayAccepted=False,oneAttemptPerValidCase=True,driverSha256=expected,completeGame=False),indent=2)+'\n')
for character,subtype in itertools.product(range(3),range(2)):
 name=f'c{character}-s{subtype}-d4-v2';p=H/name;reused=p.exists();assert sha(driver)==expected
 code=0
 if not reused:
  with(H/(name+'.log')).open('xb')as f:q=subprocess.run(['C:/nvm4w/nodejs/node.exe',str(driver),str(character),str(subtype),'4'],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=230,creationflags=subprocess.CREATE_NO_WINDOW)
  code=q.returncode
 j=load(p/'report.json');assert j['driverSha256']==expected
 passed=not code and j['terminal']and j['passed']and j['retired']and j['difficulty']==4 and j['checkpoints'][0]['state'][1]==7
 row=dict(character=character,subtype=subtype,difficulty=4,path=name,passed=passed,reusedExistingCase=reused,reportSha256=sha(p/'report.json'));rows.append(row)
 (H/'extra-matrix-progress.json').write_text(json.dumps(dict(pid=os.getpid(),completed=len(rows),total=6,cases=rows),indent=2)+'\n');print(json.dumps(row),flush=True)
 if not passed:break
j=dict(terminal=True,completed=len(rows),total=6,passed=len(rows)==6 and all(x['passed']for x in rows),cases=rows,ordinaryExtraMenuInputs=True,controlledExternalUnlockedSave=True,unlockEarnedThroughPlayAccepted=False,fullExtraRunsAccepted=False,hardwareVisualsAccepted=False,completeGame=False)
(H/'extra-matrix-report.json').write_text(json.dumps(j,indent=2)+'\n')
if not j['passed']:raise SystemExit(1)
