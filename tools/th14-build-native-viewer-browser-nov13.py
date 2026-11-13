"""Rebuild one normal Application unit and replay transport runtime."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,tempfile
R=Path(__file__).resolve().parents[1];P=R/'artifacts/th14/replay-description-bridge-nov13/browser';O=R/'artifacts/th14/native-viewer-application-nov13/browser'
if O.exists():assert not list(O.iterdir()),'Do not restart an existing browser build'
else:O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
parent=load(P/'build.json');bindings={n:sha(R/n)for n in parent['sourceBindings']}
changes={n for n,h in bindings.items()if h!=parent['sourceBindings'][n]}
assert changes=={'runtimes/th12/th12_web/cpp/sdl/Application.cpp','runtimes/th12/th12_web/sdl-runtime/shell.mjs','runtimes/th12/th12_web/sdl-runtime/eagler-host.mjs'},changes
shell_source='runtimes/th12/th12_web/sdl-runtime/shell.mjs';bindings[shell_source]=sha(R/shell_source)
host_source='runtimes/th12/th12_web/sdl-runtime/eagler-host.mjs';bindings[host_source]=sha(R/host_source)
header='runtimes/th12/portable/sdl/ReplayViewerClockTh14.hpp';bindings[header]=sha(R/header)
sdk=R/'tools/emsdk';cc=sdk/'upstream/emscripten/emcc.py';env=dict(os.environ,EMSDK=str(sdk),EMSDK_PYTHON=sys.executable,EMCC_CORES='1',EM_CONFIG=str(sdk/'.emscripten'))
objects={};changed=[]
with tempfile.TemporaryDirectory(dir=O,prefix='emsdk-')as temp:
 env.update(TEMP=temp,TMP=temp,TMPDIR=temp)
 for n,h in parent['objects'].items():
  before=P/n;assert sha(before)==h,n;target=O/n;target.parent.mkdir(parents=True,exist_ok=True)
  if Path(n).name=='th12_web_cpp_sdl_Application.cpp.o':
   source=R/'runtimes/th12/th12_web/cpp/sdl/Application.cpp'
   cmd=[sys.executable,str(cc),*[f for f in parent['flags']if f!='--profiling-funcs'],'-c',str(source),'-o',str(target)]
   with(O/'application-compile.log').open('wb')as f:q=subprocess.run(cmd,cwd=R/'runtimes/th12',env=env,stdout=f,stderr=subprocess.STDOUT,timeout=180)
   assert q.returncode==0,(O/'application-compile.log').read_text(errors='replace')[-3000:];changed.append(source.relative_to(R).as_posix())
  else:os.link(before,target)
  objects[n]=sha(target)
 assert len(objects)==146 and len(changed)==1
 link=[f+',_th14_replay_open_ready,_th14_open_replay,_th14_replay_status,_th14_replay_seek_step,_th14_replay_rate,_th14_replay_close'if f.startswith('-sEXPORTED_FUNCTIONS=')else f for f in parent['linkFlags']]
 cmd=[sys.executable,str(cc),*parent['flags'],*[str(O/n)for n in objects],*link,'-o',str(O/'th14-sdl.mjs')]
 with(O/'link.log').open('wb')as f:q=subprocess.run(cmd,cwd=R/'runtimes/th12',env=env,stdout=f,stderr=subprocess.STDOUT,timeout=240)
 assert q.returncode==0,(O/'link.log').read_text(errors='replace')[-3000:]
for n,row in parent['runtimeFiles'].items():
 assert sha(P/n)==row['sha256'],n
 if n not in ['th14-sdl.mjs','th14-sdl.wasm']:shutil.copyfile(P/n,O/n)
# Preserve established per-title path/manifest and service substitutions.
shell=O/'shell.mjs';s=(P/'shell.mjs').read_text();canonical=(R/'runtimes/th12/th12_web/sdl-runtime/shell.mjs').read_text()
a=canonical.index(" case 'playback':");b=canonical.index(" case 'sync':",a)
x=s.index(" case 'playback':");y=s.index(" case 'sync':",x);s=s[:x]+canonical[a:b]+s[y:]
start=canonical.index('function replayPlayback(){');end=canonical.index('async function command(m){',start)
s=s.replace('async function command(m){',canonical[start:end].replace('/savesth11','/savesth14')+'async function command(m){',1)
s=s.replace('isSupersededRuntimeError} from','isSupersededRuntimeError,createReplayViewerHostTh14} from',1)
s=s.replace('let th14PageLeaving=false;','let th14PageLeaving=false;\nlet replayViewer=null;',1)
s=s.replace('async function resumeForegroundAudio(forcePause=false){','async function resumeForegroundAudio(forcePause=false){\n if(replayViewer?.state&&(replayViewer.state.paused||replayViewer.state.seeking||replayViewer.state.ended)){await replayViewer.foreground();return false;}',1)
s=s.replace('core.th11_loop_stop();await save();','core.th11_loop_stop();if(replayViewer)await replayViewer.close();await save();',1)
shell.write_text(s,newline='\n')
host=O/'eagler-host.mjs';s=host.read_text();canonical=(R/host_source).read_text();marker='export function createReplayViewerHostTh14';assert marker not in s
host.write_text(s+'\n'+canonical[canonical.index(marker):],newline='\n')
for n,h in bindings.items():assert sha(R/n)==h,n
files={n:dict(bytes=(O/n).stat().st_size,sha256=sha(O/n))for n in parent['runtimeFiles']}
files['shell.mjs']=dict(bytes=shell.stat().st_size,sha256=sha(shell))
j=dict(parent,module=str(O/'th14-sdl.wasm'),sourceBindings=bindings,objects=objects,runtimeFiles=files,linkFlags=link,
 sha256=files['th14-sdl.wasm']['sha256'],loaderSha256=files['th14-sdl.mjs']['sha256'],unitsRecompiled=1,objectsVerifiedReused=145,
 sourceChanges=[dict(path=n,beforeSha256=parent['sourceBindings'].get(n),afterSha256=bindings[n])for n in sorted(changes|{header,shell_source,host_source})],
 normalAccessControl=True,parentBuildSha256=sha(P/'build.json'),toolSha256=sha(Path(__file__)),
 acceptanceStandard='observable-behavior-alignment',browserUiAccepted=False,deployed=False,completeGame=False)
(O/'build.json').write_text(json.dumps(j,indent=2)+'\n');print(json.dumps({k:j[k]for k in ['sha256','loaderSha256','unitsRecompiled','objectsVerifiedReused','deployed']}))
