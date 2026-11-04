"""Expand camera observation across existing finite mode recordings; preserve failures."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,subprocess,time
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
for name in ['output','case-plan','build']:p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();O=a.output.resolve();assert O.is_relative_to(R/'artifacts/th14') and not O.exists();O.mkdir()
sha=lambda b:hashlib.sha256(b).hexdigest()
old=a.case_plan.resolve(strict=True);assert old.is_relative_to(R/'artifacts/th14');plan=json.loads(old.read_bytes())
build=a.build.resolve(strict=True);assert build.is_relative_to(R/'artifacts/th14')
assert json.loads(build.read_bytes())['readOnlyObserver']
spec=importlib.util.spec_from_file_location('storage',R/'tools/th14-test-storage.py');storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage)
(O/'plan.json').write_bytes((json.dumps(dict(previousPlanSha256=sha(old.read_bytes()),cases=plan['cases'],buildSha256=sha(build.read_bytes()),maximumSecondsPerCase=240,maximumObservationMiBPerCase=128,minimumFreeGiB=100,hostClockOverridesAdded=False,completeGame=False),indent=2)+'\n').encode())
results=[]
for case in plan['cases']:
 native=R/case['native'];nr=json.loads((native/'report.json').read_bytes());d=O/case['key'];d.mkdir()
 row=dict(key=case['key'],callbacks=nr['callbacks'],native=case['native'],nativeReportSha256=sha((native/'report.json').read_bytes()))
 if nr['debugErrors']:
  row.update(notRun=True,reason='Retained native record rejected for debug exceptions',exceptions=len(nr['debugErrors']))
 else:
  driver=R/'tools'/('th14-compare-native-extra-full-camera-nov04.mjs' if 'extra' in case['driver'] else 'th14-compare-native-full-camera-nov04.mjs')
  cmd=['C:/nvm4w/nodejs/node.exe','--no-warnings',str(driver),'--native',str(native),'--assets',str(R/case['assets']),'--build',str(build),'--output',str(d/'model'),'--selection',','.join(map(str,case['selection'])),'--scheduler-phases','observed']
  (d/'argv.json').write_bytes((json.dumps(cmd,indent=2)+'\n').encode())
  start=time.monotonic();guard=None;storage.check_budget(d,100*1024**3,128*1024**2)
  with(d/'model.log').open('wb')as log:
   child=subprocess.Popen(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
   while child.poll()is None:
    try:storage.check_budget(d,100*1024**3,128*1024**2)
    except RuntimeError:guard='storage-budget'
    if time.monotonic()-start>240:guard='wall-budget'
    if guard:child.terminate();child.wait(timeout=30);break
    time.sleep(1)
  row.update(exitCode=child.returncode,guardStop=guard,elapsedSeconds=time.monotonic()-start,driverSha256=sha(driver.read_bytes()))
  p=d/'model/full-camera-report.json'
  if p.exists():
   full=json.loads(p.read_bytes());row.update(expandedEqual=full['allExpandedCapturedWordsEqual'],counts=full['counts'],first=full['first'][:1],words=full['callbacksCompared']*71)
 results.append(row)
 summary=dict(cases=results,casesCompleted=len(results),expandedPasses=sum(x.get('expandedEqual',False)and x.get('exitCode')==0 for x in results),completeGame=False,independentTimingAccepted=False)
 (O/'progress.json').write_bytes((json.dumps(summary,indent=2)+'\n').encode());print(json.dumps(row),flush=True)
 if row.get('guardStop'):raise SystemExit(1)
(O/'end.json').write_bytes((json.dumps(summary,indent=2)+'\n').encode())
