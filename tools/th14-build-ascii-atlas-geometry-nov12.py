from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/ascii-atlas-geometry-nov12';O=H/'component';assert not O.exists();O.mkdir();load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();parent=load(R/'artifacts/th14/ascii-queue-layout-nov12/current-provider-bindings.json');cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==parent['compilerSha256'];fixture=R/'tools/th14-ascii-atlas-geometry-component-nov12.cpp';objects={}
for path,digest in parent['sourceBindings'].items():assert sha(R/path)==digest,path
for row in parent['currentProviders']:
 p=Path(row['object']);assert sha(p)==row['objectSha256'];objects[p.relative_to(R).as_posix()]=row['objectSha256']
assert len(objects)==141
command=[str(cc),*parent['flags'],'-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(fixture),*[str(R/p) for p in objects],'-o',str(O/'probe.wasm')]
with (O/'link.log').open('wb') as log:subprocess.run(command,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120,env={**os.environ,'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)})
report=dict(normalProviderAccess=True,all141CurrentGameUnitsReverified=True,actualAsciiTextAnmRendererAndResourceParser=True,graphicsDeviceBoundaryOnly=True,sourceBindings=parent['sourceBindings'],objectBindings=objects,fixtureSha256=sha(fixture),wasmSha256=sha(O/'probe.wasm'),newGameRuns=0,newGpuRuns=0,completeGame=False)
(O/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['sourceBindings','objectBindings']}))
