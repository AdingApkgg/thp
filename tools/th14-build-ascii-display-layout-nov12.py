"""Compare text layout at an explicitly controlled glyph-submission boundary."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/ascii-display-layout-nov12'
load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
core=load(R/'artifacts/th14/mode8-display-space-nov12/current-core/build.json')
provider=load(R/'artifacts/th14/first-present-alpha-localization-nov12/batch-state/candidate/build.json')
source=R/'runtimes/th12/th12_web/cpp/game/AsciiText.cpp';assert source.read_bytes()==(H/'before.cpp').read_bytes()
fixture=R/'tools/th14-ascii-display-layout-component-nov12.cpp';cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==core['compilerSha256']
vfs=H/'candidate-vfs.json';vfs.write_text(json.dumps({'version':0,'use-external-names':False,'roots':[{'type':'file','name':str(source),'external-contents':str(H/'candidate.cpp')}]}))
for mode in ['baseline','candidate']:
 O=H/mode;assert not O.exists();O.mkdir();flags=core['flags']+(['-ivfsoverlay',str(vfs)] if mode=='candidate' else []);objects=[]
 for p,digest in provider['objects'].items():
  obj=R/p;assert sha(obj)==digest
  if obj.name=='AnmRenderer.cpp.o':continue # Declared observation services, not the renderer.
  if mode=='candidate' and obj.name=='AsciiText.cpp.o':
   obj=O/'AsciiText.cpp.o'
   with (O/'compile.log').open('wb') as log:subprocess.run([str(cc),*flags,'-c',str(source),'-o',str(obj)],cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
  objects.append(obj)
 assert len(objects)==140
 command=[str(cc),*flags,'-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(fixture),*[str(p) for p in objects],'-o',str(O/'probe.wasm')]
 with (O/'build.log').open('wb') as log:subprocess.run(command,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120,env={**os.environ,'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)})
 report=dict(mode=mode,wasmSha256=sha(O/'probe.wasm'),fixtureSha256=sha(fixture),sourceSha256=sha(H/'candidate.cpp' if mode=='candidate' else source),objects={p.relative_to(R).as_posix():sha(p) for p in objects},normalProviderAccess=True,rendererGeometryAndGpuDeclaredServices=True,syntheticAtlas=True,newGameRuns=0,newGpuRuns=0,completeGame=False)
 (O/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(mode=mode,compiled=True)),flush=True)
