"""Finite retail dialogue matrix; retain each completed original trace separately."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/th14/dialogue-real-message-matrix';OUT.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
worker=ROOT/'tools/th14-dialogue-real-message-matrix-native.py';worker_hash=sha(worker.read_bytes());jobs=[];resources={};messages={};entries=0;exe=None;d3dx=None
for stage in range(1,8):
 for selection in range(6):
  path=OUT/f'stage{stage}-selection{selection}.json';old=json.loads(path.read_bytes()) if path.exists() else None
  if not old or old.get('toolSha256')!=worker_hash:
   result=subprocess.run([sys.executable,str(worker),str(stage),str(selection)],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
   (OUT/f'stage{stage}-selection{selection}.log').write_bytes(result.stdout)
   if result.returncode:print(result.stdout.decode('utf-8',errors='replace'),flush=True);result.check_returncode()
  batch=json.loads(path.read_bytes());assert batch['toolSha256']==worker_hash
  assert all(r['frames'][-1]['status']==1 for r in batch['rows'])
  jobs.append(dict(stage=stage,selection=selection,path=path.relative_to(ROOT).as_posix(),sha256=sha(path.read_bytes()),entries=len(batch['rows'])))
  resources.update(batch['resourceHashes']);messages[batch['messageFile']]=batch['messageSha256'];entries+=len(batch['rows']);exe=batch['executableSha256'];d3dx=batch['d3dxSha256']
  print(f'Matrix original completed stage{stage} selection{selection}: {len(jobs)}/42 files, {entries}/90 entries',flush=True)
assert entries==90
report=dict(passed=True,entries=entries,jobs=jobs,resourceHashes=resources,messageHashes=messages,executableSha256=exe,d3dxSha256=d3dx,toolSha256=sha(Path(__file__).read_bytes()),workerSha256=worker_hash,scope='All90 real original MSG entry programs across seven stages/six shot selections, full original431a70/432400/42e6f0 and430d6b..430dfe owner block and real text/front/player/enemy/logo/alternate enemy ANM factories/lifetimes/36-layer geometry. Actual4321c2..4321de native MSG table lookup; original full file loader/world/HUD/input/music/audio/text device boundary controlled. Every60frame confirmation at rate1; no GDI/GPU/fullworld/naturalclear equivalence.')
(ROOT/'artifacts/th14/dialogue-real-message-matrix-native.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('PASS original real MSG matrix 90 entries',flush=True)
