from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/ascii-queue-layout-nov12';load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';fixture=R/'tools/th14-hud-queue-layout-component-nov12.cpp'
for mode in ['baseline','candidate']:
 parent=load(H/mode/'build.json');assert sha(cc)==parent['compilerSha256'];O=H/('hud-'+mode);assert not O.exists();O.mkdir();objects=[]
 for row in parent['objects']:
  p=R/row['object'];assert sha(p)==row['sha256']
  if Path(row['source']).name!='AnmRenderer.cpp':objects.append(p)
 assert len(objects)==140
 command=[str(cc),*parent['flags'],'-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(fixture),*[str(p) for p in objects],'-o',str(O/'probe.wasm')]
 with (O/'link.log').open('wb') as log:subprocess.run(command,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120,env={**os.environ,'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)})
 report=dict(mode=mode,wasmSha256=sha(O/'probe.wasm'),fixtureSha256=sha(fixture),normalProviderAccess=True,objects={p.relative_to(R).as_posix():sha(p) for p in objects},rendererGeometryAndGpuDeclaredServices=True,syntheticAtlas=True,newGameRuns=0,newGpuRuns=0,completeGame=False)
 (O/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(mode=mode,hudCompiled=True)))
