"""Link the adopted clean core with a real quiet Application/GLES observer."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/mode8-display-space-nov12';O=H/'application/component'
assert not O.exists();O.mkdir(parents=True);(O/'objects').mkdir()
load=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
C=H/'current-core';core=load(C/'build.json');B=R/'artifacts/th14/control-main-stop-nov12/first-present/probe-v2'
prior=load(B/'candidate/build.json');adopt=load(H/'source-adoption.json');changed={x['path'] for x in adopt['files']}
for p,d in prior['sourceBindingsByMode']['candidate'].items():
 if p not in changed:assert sha(R/p)==d,p
for p,d in core['sourceBindings'].items():assert sha(R/p)==d,p
assert sha(B/'fixture.cpp')==prior['fixtureSha256']
bindings=dict(core['sourceBindings'])
for name in ['Application.cpp','InitialCppResourcesTh14.hpp','Th14WarmAttractCase.hpp','fixture.cpp']:
 p=O/name;p.write_bytes((B/name).read_bytes());bindings[p.relative_to(R).as_posix()]=sha(p)
rt=R/'runtimes/th12';cc=rt/'tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==core['compilerSha256']
flags=core['flags']+['-I'+str(rt/'th12_web/cpp/sdl'),'-I'+str(rt/'portable/sdl'),'-I'+str(R/'artifacts/th14/boot-main-intake-nov07/application-component/include')]
env={**os.environ,'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)}
objects={Path(x['object']).relative_to(R).as_posix():x['objectSha256'] for x in core['currentProviders']}
for name in ['th12_web/cpp/sdl/AudioDevice.cpp','th12_web/cpp/sdl/FontDevice.cpp','th12_web/cpp/sdl/GraphicsDevice.cpp','portable/sdl/Renderer.cpp']:
 p=rt/name;bindings[p.relative_to(R).as_posix()]=sha(p);obj=O/'objects'/(p.name+'.o')
 cmd=[str(cc),*flags,'-c',str(p),'-o',str(obj)]
 with (obj.with_suffix('.log')).open('wb') as f:subprocess.run(cmd,cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=240)
 objects[obj.relative_to(R).as_posix()]=sha(obj)
bindings[(rt/'th12_web/cpp/sdl/Application.cpp').relative_to(R).as_posix()]=sha(rt/'th12_web/cpp/sdl/Application.cpp')
cmd=[str(cc),*flags,'-fno-access-control','-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined',
 '-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(O/'fixture.cpp'),*[str(R/p) for p in objects],'-o',str(O/'candidate.wasm')]
with (O/'link.log').open('wb') as f:subprocess.run(cmd,cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=240)
(O/'command.json').write_text(json.dumps(cmd,indent=2)+'\n')
bindings[Path(__file__).relative_to(R).as_posix()]=sha(Path(__file__))
report=dict(actualColdApplicationInitializeTickAndDraw=True,noDeclaredPerFileReadinessSchedule=True,
 sourceBindingsByMode={'candidate':bindings},objectBindings=objects,fixturePath=(O/'fixture.cpp').relative_to(R).as_posix(),fixtureSha256=sha(O/'fixture.cpp'),
 outputs={'candidate':{'wasmSha256':sha(O/'candidate.wasm')}},wasmSha256=sha(O/'candidate.wasm'),
 normalEngineAccessControl=True,fixtureOnlyRelaxedAccess=True,frozenCurrentApplicationWithExistingReadObservers=True,
 gameProvidersFreshFromCurrentSource=141,hostProvidersFreshFromCurrentSource=4,observationStride=49,
 baselineGameSource='e6b15d27768ee4da293c81c3c239e3d42880020b',adoptedMode8ChangeSha256=sha(H/'source-adoption.json'),
 completeGame=False)
(O/'build.json').write_text(json.dumps(report,indent=2)+'\n')
(O/'actual-link-object-bindings.json').write_text(json.dumps(dict(actualLinkObjectBindings=objects),indent=2)+'\n')
print(json.dumps(dict(compiled=True,normalProviders=145,wasmSha256=report['wasmSha256'])))
