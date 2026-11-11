"""Recompile every browser unit after TH14's text-style layout changes."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,os,subprocess,sys,time
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/ascii-queue-layout-nov12';O=H/'browser';load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();q=load(H/'qualified.json');assert q['sourceAdopted'] and q['allBrowserUnitsMustBeRebuilt'];assert not O.exists();O.mkdir();(O/'objects').mkdir();(O/'logs').mkdir()
P=R/'artifacts/th14/ascii-display-layout-nov12/browser';parent=load(P/'build.json');clean=load(R/'artifacts/th14/mode8-display-space-nov12/browser/build.json');bindings={p:sha(R/p) for p in parent['sourceBindings']};assert bindings==q['currentSourceBindings']
runtime=R/'runtimes/th12';sdk=runtime/'tools/emsdk';compiler=sdk/'upstream/emscripten/emcc.py';configuration=sdk/'.emscripten';assert sha(compiler)==parent['compilerSha256'] and sha(configuration)==parent['configurationSha256'];env={**os.environ,'EM_CONFIG':str(configuration),'EMSDK':str(sdk),'EMSDK_PYTHON':sys.executable,'EMCC_CORES':'2','TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)}
assert len(parent['objects'])==146 and len({Path(r['source']).name for r in parent['objects']})==146
started=time.monotonic()
def compile_unit(row):
 source=R/row['source'];obj=O/'objects'/(source.name+'.o')
 with (O/'logs'/(source.name+'.log')).open('wb') as log:subprocess.run([sys.executable,str(compiler),*clean['flags'],'-c',str(source),'-o',str(obj)],cwd=runtime,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
 return dict(source=row['source'],sourceSha256=sha(source),object=obj.relative_to(R).as_posix(),sha256=sha(obj),freshlyCompiled=True)
with ThreadPoolExecutor(max_workers=2) as pool:records=list(pool.map(compile_unit,parent['objects']))
objects=[str(R/r['object']) for r in records]
with (O/'logs/link.log').open('wb') as log:subprocess.run([sys.executable,str(compiler),*clean['flags'],*objects,*clean['linkFlags'],'-o',str(O/'th14-sdl.mjs')],cwd=runtime,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=300)
for p,digest in bindings.items():assert sha(R/p)==digest,p
for p in P.glob('*.mjs'):
 if p.name!='th14-sdl.mjs':(O/p.name).write_bytes(p.read_bytes())
report=dict(units=146,freshlyCompiledUnits=146,reusedUnits=0,sourceBindings=bindings,objects=records,flags=clean['flags'],linkFlags=clean['linkFlags'],sha256=sha(O/'th14-sdl.wasm'),loaderSha256=sha(O/'th14-sdl.mjs'),compilerSha256=sha(compiler),configurationSha256=sha(configuration),elapsedSeconds=time.monotonic()-started,normalProductionAccess=True,fixtureMacrosOrVfsUsed=False,browserUiAcceptance=False,newGameRuns=0,newGpuRuns=0,audibleOutput=False,completeGame=False)
(O/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['sourceBindings','objects','flags','linkFlags']}))
