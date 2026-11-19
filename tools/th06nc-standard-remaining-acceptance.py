"""Run remaining representative Standard natural recordings and full replays.

Uses existing browser acceptance tools sequentially on the dedicated CDP port.
Stops on any child failure, retaining its complete log and stage information.
This is an execution queue, not a claim that every Standard combination passes.
"""
import json,socket,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
 if '--wait-for-hard-record'in sys.argv:
  log=ROOT/'tools/tmp/th06nc-standard-reimu-b-hard-natural-fixed-ending.log';deadline=time.monotonic()+3600
  while time.monotonic()<deadline:
   tail=log.read_text(encoding='utf-8',errors='replace')[-6000:]if log.exists()else ''
   if 'AssertionError'in tail or 'Error:'in tail:raise SystemExit('Hard recording failed; inspect '+str(log))
   if '"passed":true'in tail:
    try:
     with socket.create_connection(('127.0.0.1',9499),timeout=.5):pass
    except OSError:break
   time.sleep(2)
  else:raise SystemExit('Timed out waiting for the active Hard recording')
 jobs=[('hard-reimu-b-playback',['tools/th06nc-natural-playback-browser-check.mjs','--standard','--profile=1','--difficulty=2']),
       ('hard-reimu-b-earned-extra',['tools/th06nc-earned-extra-browser-check.mjs','--profile=1','--difficulty=2']),
       ('lunatic-marisa-b-record',['tools/th06nc-standard-natural-browser-check.mjs','--planner','--no-continue','--pool-snapshots','--profile=3','--difficulty=3']),
       ('lunatic-marisa-b-playback',['tools/th06nc-natural-playback-browser-check.mjs','--standard','--profile=3','--difficulty=3']),
       ('lunatic-marisa-b-earned-extra',['tools/th06nc-earned-extra-browser-check.mjs','--profile=3','--difficulty=3']),
       ('easy-marisa-a-record',['tools/th06nc-standard-natural-browser-check.mjs','--planner','--no-continue','--pool-snapshots','--profile=2','--difficulty=0']),
       ('easy-marisa-a-playback',['tools/th06nc-natural-playback-browser-check.mjs','--standard','--profile=2','--difficulty=0']),
       ('normal-reimu-a-current-playback',['tools/th06nc-natural-playback-browser-check.mjs','--standard','--revalidate-source','--profile=0','--difficulty=1'])]
 rows=[];progress=ROOT/'tools/tmp/th06nc-standard-remaining-progress.json'
 for name,args in jobs:
  log=ROOT/'tools/tmp'/('th06nc-'+name+'.log');state=dict(active=name,completed=rows,complete=False);progress.write_text(json.dumps(state,indent=2)+'\n');print(json.dumps(dict(start=name,log=str(log))),flush=True);start=time.monotonic()
  with log.open('w',encoding='utf-8')as out:result=subprocess.run(['node',*args],cwd=ROOT,stdout=out,stderr=subprocess.STDOUT)
  row=dict(name=name,returncode=result.returncode,seconds=round(time.monotonic()-start,2),log=log.relative_to(ROOT).as_posix());rows.append(row);print(json.dumps(row),flush=True)
  if result.returncode:
   progress.write_text(json.dumps(dict(active=None,completed=rows,complete=False,failed=name),indent=2)+'\n');raise SystemExit(result.returncode)
 progress.write_text(json.dumps(dict(active=None,completed=rows,complete=True),indent=2)+'\n');print(json.dumps(dict(completed=len(rows))),flush=True)
if __name__=='__main__':main()
