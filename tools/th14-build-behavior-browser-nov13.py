"""Current behavior candidate: two fresh normal units,144 verified objects."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,tempfile
R=Path(__file__).resolve().parents[1];P=R/'artifacts/th14/replay-save-reopen-nov13/browser';O=R/'artifacts/th14/behavior-matrix-nov13/browser';assert not O.exists();O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
parent=load(P/'build.json');bindings={n:sha(R/n)for n in parent['sourceBindings']}
changes={n for n,h in bindings.items()if h!=parent['sourceBindings'][n]}
expected={'runtimes/th12/portable/sdl/Renderer.cpp','runtimes/th12/th12_web/cpp/game/SceneCompositor.cpp'};assert changes==expected,changes
profile=load(R/'tools/th14-gles-profile.json');assert profile['flags']==parent['flags']and'-fno-access-control'not in parent['flags']
sdk=R/'tools/emsdk';cc=sdk/'upstream/emscripten/emcc.py';env=dict(os.environ,EMSDK=str(sdk),EMSDK_PYTHON=sys.executable,EMCC_CORES='1',EM_CONFIG=str(sdk/'.emscripten'))
objects={};changed=[]
with tempfile.TemporaryDirectory(dir=O,prefix='emsdk-')as temp:
 env.update(TEMP=temp,TMP=temp,TMPDIR=temp)
 for n,h in parent['objects'].items():
  before=P/n;assert sha(before)==h,n;target=O/n;target.parent.mkdir(parents=True,exist_ok=True)
  file=Path(n.replace('\\','/')).name
  source=R/'runtimes/th12/portable/sdl/Renderer.cpp'if file=='portable_sdl_Renderer.cpp.o'else R/'runtimes/th12/th12_web/cpp/game/SceneCompositor.cpp'if file=='th12_web_cpp_game_SceneCompositor.cpp.o'else None
  if source:
   cmd=[sys.executable,str(cc),*[f for f in parent['flags']if f!='--profiling-funcs'],'-c',str(source),'-o',str(target)]
   with(O/(file+'.log')).open('wb')as f:q=subprocess.run(cmd,cwd=R/'runtimes/th12',env=env,stdout=f,stderr=subprocess.STDOUT,timeout=180)
   assert q.returncode==0,(O/(file+'.log')).read_text(errors='replace')[-3000:];changed.append(source.relative_to(R).as_posix())
  else:os.link(before,target)
  objects[n]=sha(target)
 assert len(objects)==146 and len(changed)==2
 cmd=[sys.executable,str(cc),*parent['flags'],*[str(O/n)for n in objects],*parent['linkFlags'],'-o',str(O/'th14-sdl.mjs')]
 with(O/'link.log').open('wb')as f:q=subprocess.run(cmd,cwd=R/'runtimes/th12',env=env,stdout=f,stderr=subprocess.STDOUT,timeout=240)
 assert q.returncode==0,(O/'link.log').read_text(errors='replace')[-3000:]
for n,row in parent['runtimeFiles'].items():
 assert sha(P/n)==row['sha256'],n
 if n not in ['th14-sdl.mjs','th14-sdl.wasm']:shutil.copyfile(P/n,O/n)
for n,h in bindings.items():assert sha(R/n)==h,n
files={n:dict(bytes=(O/n).stat().st_size,sha256=sha(O/n))for n in parent['runtimeFiles']}
j=dict(parent,module=str(O/'th14-sdl.wasm'),sourceBindings=bindings,objects=objects,runtimeFiles=files,
 sha256=files['th14-sdl.wasm']['sha256'],loaderSha256=files['th14-sdl.mjs']['sha256'],unitsRecompiled=2,objectsVerifiedReused=144,
 sourceChanges=[dict(path=n,beforeSha256=parent['sourceBindings'][n],afterSha256=bindings[n])for n in sorted(changes)],
 normalAccessControl=True,parentBuildSha256=sha(P/'build.json'),toolSha256=sha(Path(__file__)),
 acceptanceStandard='observable-behavior-alignment',browserUiAccepted=False,deployed=False,completeGame=False)
(O/'build.json').write_text(json.dumps(j,indent=2)+'\n');print(json.dumps({k:j[k]for k in ['sha256','loaderSha256','unitsRecompiled','objectsVerifiedReused','deployed']}))
