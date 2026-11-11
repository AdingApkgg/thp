"""Compile the sole changed browser TU and relink145 hash-verified objects."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/quad-display-space-nov12';O=H/'browser';assert not O.exists();O.mkdir();(O/'logs').mkdir();load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();P=R/'artifacts/th14/mode8-display-space-nov12/browser';parent=load(P/'build.json');q=load(H/'qualified.json');assert q['sourceAdopted'];bindings={p:sha(R/p)for p in parent['sourceBindings']};changed=[p for p in bindings if bindings[p]!=parent['sourceBindings'][p]];assert changed==['runtimes/th12/th12_web/cpp/game/AnmRenderer.cpp']
runtime=R/'runtimes/th12';sdk=runtime/'tools/emsdk';compiler=sdk/'upstream/emscripten/emcc.py';configuration=sdk/'.emscripten';assert sha(compiler)==parent['toolchain']['compilerSha256']and sha(configuration)==parent['toolchain']['configurationSha256'];env={**os.environ,'EM_CONFIG':str(configuration),'EMSDK':str(sdk),'EMSDK_PYTHON':sys.executable,'EMCC_CORES':'2','TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)};started=time.monotonic();objects=[];records=[]
for row in parent['compileResults']:
 obj=R/row['object'];assert sha(obj)==row['sha256']
 if row['source']==changed[0]:
  obj=O/'AnmRenderer.cpp.o';cmd=[sys.executable,str(compiler),*parent['flags'],'-c',str(R/row['source']),'-o',str(obj)]
  with(O/'logs/compile.log').open('wb')as f:subprocess.run(cmd,cwd=runtime,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=180)
 objects.append(str(obj));records.append(dict(source=row['source'],object=obj.relative_to(R).as_posix(),sha256=sha(obj),freshlyCompiled=row['source']==changed[0]))
cmd=[sys.executable,str(compiler),*parent['flags'],*objects,*parent['linkFlags'],'-o',str(O/'th14-sdl.mjs')]
with(O/'logs/link.log').open('wb')as f:subprocess.run(cmd,cwd=runtime,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=300)
for p,d in bindings.items():assert sha(R/p)==d,p
for p in P.glob('*.mjs'):
 if p.name!='th14-sdl.mjs':(O/p.name).write_bytes(p.read_bytes())
report=dict(units=146,freshlyCompiledUnits=1,reusedAndHashVerifiedUnits=145,changedSourceInputs=changed,sourceBindings=bindings,objects=records,sha256=sha(O/'th14-sdl.wasm'),loaderSha256=sha(O/'th14-sdl.mjs'),parentBuild='artifacts/th14/mode8-display-space-nov12/browser/build.json',compilerSha256=sha(compiler),configurationSha256=sha(configuration),elapsedSeconds=time.monotonic()-started,browserUiAcceptance=False,audibleOutput=False,completeGame=False)
(O/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k not in ['sourceBindings','objects']}))
