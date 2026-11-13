"""Publish only reviewed viewer source and finite evidence; never game data."""
from pathlib import Path
import base64,hashlib,json,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/native-viewer-application-nov13';O=H/'publication';O.mkdir(exist_ok=False)
gh='C:/Program Files/GitHub CLI/gh.exe';repo='repos/AdingApkgg/thp'
proof=json.loads((R/'docs/porting/th14-native-viewer-nov13.json').read_bytes());assert not proof['completeGame'] and proof['actualApplicationAndCppThreads']
files=[
 'runtimes/th12/portable/sdl/ReplayViewerClockTh14.hpp',
 'runtimes/th12/th12_web/cpp/sdl/Application.cpp',
 'runtimes/th12/th12_web/sdl-runtime/eagler-host.mjs',
 'runtimes/th12/th12_web/sdl-runtime/shell.mjs',
 'tools/th14-build-native-viewer-application-nov13.py',
 'tools/th14-check-native-viewer-application-nov13.mjs',
 'tools/th14-check-multistage-native-viewer-nov13.mjs',
 'tools/th14-build-native-viewer-browser-nov13.py',
 'tools/th14-check-replay-description-bridge-nov13.mjs',
 'tools/th14-qualify-native-viewer-nov13.py',
 'tools/th14-publish-native-viewer-nov13.py',
 'docs/porting/TH14_NATIVE_VIEWER_NOV13.md',
 'docs/porting/th14-native-viewer-nov13.json']
snapshots={n:(R/n).read_bytes()for n in files};assert len(snapshots)==len(files) and sum(map(len,snapshots.values()))<400000
def api(path,method=None,payload=None):
 cmd=[gh,'api',repo+'/'+path]
 if method:cmd+=['--method',method]
 if payload is not None:
  request=O/'request.json';request.write_text(json.dumps(payload),encoding='utf8');cmd+=['--input',str(request)]
 q=subprocess.run(cmd,cwd=R,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
 assert q.returncode==0,q.stderr.decode('utf8','replace')[:1500]
 return json.loads(q.stdout)
parent=api('git/ref/heads/main')['object']['sha'];assert parent=='bc9f3ee7c960812120cd59fecba26374c65d8c7d',parent
base_tree=api('git/commits/'+parent)['tree']['sha'];tree=[]
for n,b in snapshots.items():
 blob=api('git/blobs','POST',dict(content=base64.b64encode(b).decode(),encoding='base64'))['sha']
 assert blob==hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest(),n
 tree.append(dict(path=n,mode='100644',type='blob',sha=blob))
(O/'reviewed-plan.json').write_text(json.dumps(dict(parent=parent,files={n:dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())for n,b in snapshots.items()},noRawAssetsSavesReplaysOrBinaries=True),indent=2)+'\n')
new_tree=api('git/trees','POST',dict(base_tree=base_tree,tree=tree))['sha']
commit=api('git/commits','POST',dict(message='Implement native TH14 hosted replay controls and qualify finite transport cases\n\nUse actual Application replay sessions for pause/play, bounded seek, rate and selected-stage playback. Keep browser deployment and whole-game acceptance pending.',tree=new_tree,parents=[parent]))['sha']
assert api('git/ref/heads/main')['object']['sha']==parent,'Remote advanced; never force'
for n,b in snapshots.items():assert(R/n).read_bytes()==b,n
api('git/refs/heads/main','PATCH',dict(sha=commit,force=False));assert api('git/ref/heads/main')['object']['sha']==commit
j=dict(commit=commit,parent=parent,files=len(files),allBlobHashesVerified=True,refForce=False,noRawAssetsSavesReplaysOrBinaries=True,deployed=False,completeGame=False)
(O/'published.json').write_text(json.dumps(j,indent=2)+'\n');print(json.dumps(j),flush=True)
