"""Build a fresh normal-access TH14 core for the private queue/align candidate."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,os,subprocess,time
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/ascii-queue-layout-nov12';load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parent=load(R/'artifacts/th14/ascii-display-layout-nov12/current-provider-bindings.json');cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==parent['compilerSha256'];fixture=R/'tools/th14-ascii-queue-layout-component-nov12.cpp'
for name in ['AsciiText.cpp','AsciiText.hpp','HudTh14Text.cpp']:assert (R/'runtimes/th12/th12_web/cpp/game'/name).read_bytes()==(H/('before-'+name)).read_bytes()
for path,digest in parent['sourceBindings'].items():assert sha(R/path)==digest,path
for mode in ['baseline','candidate']:
 O=H/mode;assert not O.exists();O.mkdir();flags=parent['flags']+(['-ivfsoverlay',str(H/'candidate-vfs.json'),'-DTH14_ASCII_ALIGNMENT_CANDIDATE=1'] if mode=='candidate' else []);started=time.monotonic()
 def compile_unit(row):
  if mode=='baseline':
   obj=Path(row['object']);assert sha(obj)==row['objectSha256'];return dict(source=row['source'],object=obj.relative_to(R).as_posix(),sha256=sha(obj),freshlyCompiled=False)
  source=R/row['source'];obj=O/(source.name+'.o')
  with (O/(source.name+'.log')).open('wb') as log:subprocess.run([str(cc),*flags,'-c',str(source),'-o',str(obj)],cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
  return dict(source=row['source'],object=obj.relative_to(R).as_posix(),sha256=sha(obj),freshlyCompiled=True)
 with ThreadPoolExecutor(max_workers=2) as pool:records=list(pool.map(compile_unit,parent['currentProviders']))
 assert len(records)==141 and len({r['object'] for r in records})==141
 objects=[R/r['object'] for r in records if Path(r['source']).name!='AnmRenderer.cpp'];assert len(objects)==140
 command=[str(cc),*flags,'-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(fixture),*[str(p) for p in objects],'-o',str(O/'probe.wasm')]
 with (O/'link.log').open('wb') as log:subprocess.run(command,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120,env={**os.environ,'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)})
 bindings=dict(parent['sourceBindings'])
 if mode=='candidate':
  for name in ['AsciiText.cpp','AsciiText.hpp','HudTh14Text.cpp']:bindings['runtimes/th12/th12_web/cpp/game/'+name]=sha(H/('candidate-'+name))
 report=dict(mode=mode,flags=flags,compilerSha256=sha(cc),sourceBindings=bindings,objects=records,wasmSha256=sha(O/'probe.wasm'),fixtureSha256=sha(fixture),freshlyCompiledGameUnits=141 if mode=='candidate' else 0,normalProviderAccess=True,rendererGeometryAndGpuDeclaredServices=True,syntheticAtlas=True,stableDeviceSizeWithinQueueDrawDeclared=True,elapsedSeconds=time.monotonic()-started,newGameRuns=0,newGpuRuns=0,completeGame=False)
 (O/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['flags','sourceBindings','objects']}),flush=True)
