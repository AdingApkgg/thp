"""Fresh normal browser build after TH14 display-mode entry integration."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,os,subprocess,sys,time
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/display-mode-entry-nov12';O=H/'browser';O.mkdir(exist_ok=False);(O/'objects').mkdir();(O/'logs').mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes());q=load(H/'qualified.json');assert q['sourceAdopted']
parent=load(R/'artifacts/th14/ascii-queue-layout-nov12/browser/build.json');bindings=q['currentSourceBindings']
for path,d in bindings.items():assert sha(R/path)==d,path
assert len(bindings)==368 and len(parent['objects'])==146
rt=R/'runtimes/th12';sdk=rt/'tools/emsdk';cc=sdk/'upstream/emscripten/emcc.py';config=sdk/'.emscripten';assert sha(cc)==parent['compilerSha256'] and sha(config)==parent['configurationSha256']
env={**os.environ,'EM_CONFIG':str(config),'EMSDK':str(sdk),'EMSDK_PYTHON':sys.executable,'EMCC_CORES':'2','TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)};started=time.monotonic()
def compile_unit(row):
 source=R/row['source'];out=O/'objects'/(source.name+'.o')
 with (O/'logs'/(source.name+'.log')).open('wb') as log:subprocess.run([sys.executable,str(cc),*parent['flags'],'-c',str(source),'-o',str(out)],cwd=rt,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180,env=env)
 return dict(source=row['source'],sourceSha256=sha(source),object=out.relative_to(R).as_posix(),sha256=sha(out),freshlyCompiled=True)
with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(compile_unit,parent['objects']))
with (O/'logs/link.log').open('wb') as log:subprocess.run([sys.executable,str(cc),*parent['flags'],*[str(R/r['object']) for r in rows],*parent['linkFlags'],'-o',str(O/'th14-sdl.mjs')],cwd=rt,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=300,env=env)
for path,d in bindings.items():assert sha(R/path)==d,path
for p in (R/'artifacts/th14/ascii-queue-layout-nov12/browser').glob('*.mjs'):
 if p.name!='th14-sdl.mjs':(O/p.name).write_bytes(p.read_bytes())
report=dict(units=146,freshlyCompiledUnits=146,reusedUnits=0,sourceBindings=bindings,objects=rows,flags=parent['flags'],linkFlags=parent['linkFlags'],sha256=sha(O/'th14-sdl.wasm'),loaderSha256=sha(O/'th14-sdl.mjs'),compilerSha256=sha(cc),configurationSha256=sha(config),elapsedSeconds=time.monotonic()-started,normalProductionAccess=True,fixtureMacrosOrVfsUsed=False,browserUiAcceptance=False,audibleOutput=False,completeGame=False)
(O/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['sourceBindings','objects','flags','linkFlags']}))
