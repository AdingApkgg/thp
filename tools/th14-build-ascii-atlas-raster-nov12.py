from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/ascii-atlas-raster-nov12';O=H/'component';O.mkdir(exist_ok=False)
load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parent=load(R/'artifacts/th14/ascii-queue-layout-nov12/current-provider-bindings.json')
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==parent['compilerSha256']
for p,d in parent['sourceBindings'].items():assert sha(R/p)==d,p
objects={r['object']:r['objectSha256'] for r in parent['currentProviders']}
objects.update(parent['normalHostObjectBindings'])
for p,d in objects.items():assert sha(Path(p) if Path(p).is_absolute() else R/p)==d,p
fixture=R/'tools/th14-ascii-atlas-raster-component-nov12.cpp';rt=R/'runtimes/th12'
flags=parent['flags']+['-I'+str(rt/'th12_web/cpp/sdl'),'-I'+str(rt/'portable/sdl'),'-I'+str(R/'artifacts/th14/boot-main-intake-nov07/application-component/include')]
cmd=[str(cc),*flags,'-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(fixture),*[str(Path(p) if Path(p).is_absolute() else R/p) for p in objects],'-o',str(O/'probe.wasm')]
with (O/'link.log').open('wb') as log:subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120,env={**os.environ,'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)})
report=dict(sourceBindings=parent['sourceBindings'],objectBindings=objects,fixtureSha256=sha(fixture),wasmSha256=sha(O/'probe.wasm'),normalAccess=True,normalGameObjects=141,normalHostObjects=4,actualCppAsciiAndGraphicsDeviceAndRenderer=True,noGameSession=True,noAudioDevice=True,completeGame=False)
(O/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['sourceBindings','objectBindings']}))
