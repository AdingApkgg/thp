"""Clean 146-unit browser build for the adopted mode8 display-space fix."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,os,shutil,subprocess,sys,time
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/mode8-display-space-nov12';O=H/'browser'
assert not O.exists() and shutil.disk_usage(R).free>=100*1024**3
O.mkdir();(O/'objects').mkdir();(O/'logs').mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_bytes())
P=R/'artifacts/th14/control-main-stop-nov12/browser';parent=load(P/'build.json')
adopt=load(H/'source-adoption.json');assert adopt['adopted']
expected={x['path'] for x in adopt['files']}
changed={p for p,d in parent['sourceBindings'].items() if sha(R/p)!=d};assert changed==expected,changed
bindings={p:sha(R/p) for p in parent['sourceBindings']}
runtime=R/'runtimes/th12';sdk=runtime/'tools/emsdk';compiler=sdk/'upstream/emscripten/emcc.py';configuration=sdk/'.emscripten'
assert compiler.is_file() and configuration.is_file()
flags=parent['flags'];link=parent['linkFlags'];sources=sorted((runtime/'th12_web/cpp/game').glob('*.cpp'))+sorted((runtime/'th12_web/cpp/sdl').glob('*.cpp'))+[runtime/'portable/sdl/Renderer.cpp']
assert len(sources)==146
env={**os.environ,'EM_CONFIG':str(configuration),'EMSDK':str(sdk),'EMSDK_PYTHON':sys.executable,'EMCC_CORES':'2','TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)}
started=time.monotonic()
def compile(source):
 name=source.relative_to(runtime).as_posix().replace('/','_')+'.o';obj=O/'objects'/name
 cmd=[sys.executable,str(compiler),*flags,'-c',str(source),'-o',str(obj)]
 with (O/'logs'/(name+'.log')).open('wb') as f:subprocess.run(cmd,cwd=runtime,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=300)
 return dict(source=source.relative_to(R).as_posix(),sourceSha256=sha(source),object=obj.relative_to(R).as_posix(),sha256=sha(obj))
results=[]
with ThreadPoolExecutor(max_workers=3) as pool:
 for i,row in enumerate(pool.map(compile,sources),1):
  results.append(row)
  if i%20==0 or i==146:print(json.dumps(dict(compiled=i,total=146,elapsedSeconds=round(time.monotonic()-started,2))),flush=True)
cmd=[sys.executable,str(compiler),*flags,*[str(R/x['object']) for x in results],*link,'-o',str(O/'th14-sdl.mjs')]
(O/'link-command.json').write_text(json.dumps(cmd,indent=2)+'\n')
with (O/'logs/link.log').open('wb') as f:subprocess.run(cmd,cwd=runtime,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=600)
helpers={}
for source in P.glob('*.mjs'):
 if source.name=='th14-sdl.mjs':continue
 actual=runtime/'portable/sdl'/source.name;assert sha(actual)==sha(source),source.name
 (O/source.name).write_bytes(actual.read_bytes());helpers[source.name]=sha(actual)
for p,d in bindings.items():assert sha(R/p)==d,p
report=dict(module=str(O/'th14-sdl.wasm'),units=146,cleanBuild=True,reusedObjects=0,sourceBindings=bindings,
 objects={x['object']:x['sha256'] for x in results},compileResults=results,flags=flags,linkFlags=link,
 sha256=sha(O/'th14-sdl.wasm'),loaderSha256=sha(O/'th14-sdl.mjs'),helpers=helpers,
 toolchain=dict(compiler=str(compiler),compilerSha256=sha(compiler),configuration=str(configuration),configurationSha256=sha(configuration),python=sys.executable),
 elapsedSeconds=time.monotonic()-started,changedSourceInputs=sorted(changed),retailAssetsCopied=False,browserAcceptance=False,completeGame=False)
(O/'build.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(compiledUnits=146,wasmSha256=report['sha256'],seconds=report['elapsedSeconds'])),flush=True)
