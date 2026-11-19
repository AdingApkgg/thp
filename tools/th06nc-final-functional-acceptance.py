"""Finish queued gameplay checks, publish status metadata, then verify final UI.

Only the status literals/footer may change between gameplay acceptance and the
fresh startup/input/config/quit/Spell regressions. Stops on any failure.
"""
import json,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
 if '--wait-for-standard'in sys.argv:
  progress=ROOT/'tools/tmp/th06nc-standard-remaining-progress.json';deadline=time.monotonic()+3600
  while time.monotonic()<deadline:
   state=json.loads(progress.read_text())if progress.exists()else {}
   if state.get('failed'):raise SystemExit('Standard acceptance failed: '+state['failed'])
   if state.get('complete')is True:break
   time.sleep(2)
  else:raise SystemExit('Timed out waiting for Standard acceptance')
 py=[sys.executable,'-X','utf8'];jobs=[
  ('standard-coverage',[*py,'tools/th06nc-standard-natural-coverage-check.py']),
  ('prepare-status',[*py,'tools/th06nc-functional-completion-check.py','--prepare']),
  ('final-cold-title',['node','tools/th06nc-cold-title-browser-check.mjs','--completion']),
  ('final-input',['node','tools/th06nc-input-browser-check.mjs']),
  ('final-title-config',['node','tools/th06nc-title-config-browser-check.mjs']),
  ('final-quit',['node','tools/th06nc-quit-browser-check.mjs']),
  ('final-spell-capture',['node','tools/th06nc-spell-host-browser-check.mjs','--capture']),
  ('final-score-codec',[*py,'tools/th06nc-score-browser-files-native-check.py']),
  ('final-replay-codec',[*py,'tools/th06nc-replay-browser-files-native-check.py']),
  ('functional-completion',[*py,'tools/th06nc-functional-completion-check.py']),
  ('final-source-audit',[*py,'tools/th06nc-source-current-audit.py'])]
 rows=[];progress=ROOT/'tools/tmp/th06nc-final-functional-progress.json'
 for name,args in jobs:
  log=ROOT/'tools/tmp'/('th06nc-'+name+'.log');progress.write_text(json.dumps(dict(active=name,completed=rows,complete=False),indent=2)+'\n');print(json.dumps(dict(start=name,log=str(log))),flush=True);start=time.monotonic()
  with log.open('w',encoding='utf-8')as out:result=subprocess.run(args,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT)
  row=dict(name=name,returncode=result.returncode,seconds=round(time.monotonic()-start,2),log=log.relative_to(ROOT).as_posix());rows.append(row);print(json.dumps(row),flush=True)
  if result.returncode:
   progress.write_text(json.dumps(dict(active=None,completed=rows,complete=False,failed=name),indent=2)+'\n');raise SystemExit(result.returncode)
 progress.write_text(json.dumps(dict(active=None,completed=rows,complete=True),indent=2)+'\n');print(json.dumps(dict(completed=len(rows),passed=True)),flush=True)
if __name__=='__main__':main()
