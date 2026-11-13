from pathlib import Path
import hashlib,itertools,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/behavior-matrix-nov13'
driver=R/'tools/th14-run-gpu-behavior-entry-nov13.mjs';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
assert load(H/'qualified-30.json')['allDeclaredCasesPassed'];expected=sha(driver);rows=[]
plan=H/'gpu-matrix-plan.json';assert not plan.exists();plan.write_text(json.dumps(dict(pid=os.getpid(),cases=6,difficulty=1,actualGles=True,ordinaryKeysAndPauseEvent=True,checkpoints=['slow-shoot','paused','bomb-running','passed'],oneAttemptPerCase=True,reuseCompletedReimuBCase=True,driverSha256=expected,completeGame=False),indent=2)+'\n')
for character,subtype in itertools.product(range(3),range(2)):
 name=f'gpu-c{character}-s{subtype}-d1-v2';p=H/name;reused=p.exists();assert sha(driver)==expected
 code=0
 if not reused:
  with(H/(name+'.log')).open('xb')as f:q=subprocess.run(['C:/nvm4w/nodejs/node.exe',str(driver),str(character),str(subtype),'1'],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=230,creationflags=subprocess.CREATE_NO_WINDOW)
  code=q.returncode
 j=load(p/'report.json');platform=load(p/'platform.json');assert j['driverSha256']==expected
 passed=not code and j['terminal']and j['passed']and j['retired']and j['bombFinished']and platform['gpuContextClosed']and not platform['audibleOutput']and not any(platform['actualNativeGles']['liveObjects'].values())
 captures={}
 for n in ['slow-shoot','paused','bomb-running','passed']:
  b=(p/(n+'.bgra')).read_bytes();assert len(b)==640*480*4
  point=next(x for x in j['checkpoints']if x['name']==n);assert hashlib.sha256(b).hexdigest()==point['pixelsSha256'];captures[n]=point['pixelsSha256']
 row=dict(character=character,subtype=subtype,path=name,passed=passed,reusedExistingCase=reused,captureHashes=captures,reportSha256=sha(p/'report.json'));rows.append(row)
 (H/'gpu-matrix-progress.json').write_text(json.dumps(dict(pid=os.getpid(),completed=len(rows),total=6,cases=rows),indent=2)+'\n');print(json.dumps(dict(character=character,subtype=subtype,passed=passed,reused=reused)),flush=True)
 if not passed:break
j=dict(terminal=True,completed=len(rows),total=6,passed=len(rows)==6 and all(x['passed']for x in rows),cases=rows,actualOffscreenGles=True,ordinaryControlsAndBombLifetime=True,allCapturedImagesRequireVisualReview=True,originalPixelEqualityRequired=False,browserUiAccepted=False,completeGame=False)
(H/'gpu-matrix-report.json').write_text(json.dumps(j,indent=2)+'\n')
if not j['passed']:raise SystemExit(1)
