"""Revalidate all20 historical natural Challenge replays in isolated browsers.

Two independent CDP ports/profiles and unique result/log paths. Production
sources remain unchanged throughout; each browser verifier enforces its own
source snapshot and recorded raw actor/counter/RNG checkpoints.
"""
import concurrent.futures,json,queue,subprocess,sys,threading,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
 jobs=queue.Queue()
 for difficulty in range(5):
  for profile in range(4):jobs.put((profile,difficulty))
 lock=threading.Lock();stop=threading.Event();rows=[];active={};progress=ROOT/'tools/tmp/th06nc-challenge-current-playback-progress.json'
 def publish():progress.write_text(json.dumps(dict(active=active,completed=rows,complete=False),indent=2)+'\n')
 def worker(port):
  while not stop.is_set():
   try:profile,difficulty=jobs.get_nowait()
   except queue.Empty:return
   name=f'challenge-profile{profile}-difficulty{difficulty}';log=ROOT/'tools/tmp'/('th06nc-current-'+name+'.log');args=['node','tools/th06nc-natural-playback-browser-check.mjs','--revalidate-source',f'--profile={profile}',f'--difficulty={difficulty}',f'--cdp-port={port}']
   if difficulty==4:args.append('--extra')
   with lock:active[str(port)]=name;publish();print(json.dumps(dict(start=name,port=port,log=str(log))),flush=True)
   started=time.monotonic()
   with log.open('w',encoding='utf-8')as out:result=subprocess.run(args,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT)
   with lock:
    row=dict(profile=profile,difficulty=difficulty,returncode=result.returncode,seconds=round(time.monotonic()-started,2),log=log.relative_to(ROOT).as_posix());rows.append(row);active.pop(str(port),None)
    if result.returncode:stop.set()
    publish();print(json.dumps(row),flush=True)
   jobs.task_done()
 with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
  futures=[pool.submit(worker,port)for port in [9500,9501]]
  for future in futures:future.result()
 if stop.is_set():raise SystemExit('A Challenge playback failed; inspect the progress/log files')
 assert len(rows)==20
 result=subprocess.run([sys.executable,'-X','utf8','tools/th06nc-challenge-revalidation-matrix-check.py'],cwd=ROOT)
 if result.returncode:raise SystemExit(result.returncode)
 progress.write_text(json.dumps(dict(active={},completed=rows,complete=True),indent=2)+'\n');print(json.dumps(dict(completed=20)),flush=True)
if __name__=='__main__':main()
