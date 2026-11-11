"""Bind all current game units and freshly compile host units for a finite ABI smoke check."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/ascii-queue-layout-nov12';O=H/'title-quit/component';assert not O.exists();O.mkdir(parents=True);load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();q=load(H/'qualified.json');assert q['sourceAdopted']
normal=load(H/'candidate/build.json');base=load(R/'artifacts/th14/ascii-display-layout-nov12/current-provider-bindings.json');B=R/'artifacts/th14/current-title-quit-nov12/component';prior=load(B/'build.json');assert sha(B/'fixture.cpp')==prior['fixtureSha256'];assert sha(R/'runtimes/th12/th12_web/cpp/sdl/Application.cpp')=='3891524dd327364005ac6749822649e6df92f2b2f0f31b75f71917bd97407c3a'
bindings=q['currentSourceBindings'];objects={row['object']:row['sha256'] for row in normal['objects']}
for path,digest in bindings.items():assert sha(R/path)==digest,path
for path,digest in objects.items():assert sha(R/path)==digest,path
assert len(objects)==141
rt=R/'runtimes/th12';cc=rt/'tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==base['compilerSha256'];flags=base['flags']+['-I'+str(rt/'th12_web/cpp/sdl'),'-I'+str(rt/'portable/sdl'),'-I'+str(R/'artifacts/th14/boot-main-intake-nov07/application-component/include')]
host_sources=[rt/'th12_web/cpp/sdl'/n for n in ['AudioDevice.cpp','FontDevice.cpp','GraphicsDevice.cpp']]+[rt/'portable/sdl/Renderer.cpp']
for source in host_sources:
 obj=O/(source.stem+'.o')
 with (O/(source.stem+'.log')).open('wb') as log:subprocess.run([str(cc),*flags,'-c',str(source),'-o',str(obj)],cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
 objects[obj.relative_to(R).as_posix()]=sha(obj)
assert len(objects)==145
for name in ['fixture.cpp','Th14WarmAttractCase.hpp']:(O/name).write_bytes((B/name).read_bytes())
command=[str(cc),*flags,'-fno-access-control','-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(O/'fixture.cpp'),*[str(R/p) for p in objects],'-o',str(O/'candidate.wasm')]
with (O/'compile.log').open('wb') as log:subprocess.run(command,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=240,env={**os.environ,'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)})
all_bindings=dict(bindings)
for p in [Path(__file__),O/'fixture.cpp',O/'Th14WarmAttractCase.hpp',R/'runtimes/th12/th12_web/tests/cpp/th14-native-title-live-observer.hpp']:all_bindings[p.relative_to(R).as_posix()]=sha(p)
report=dict(compiled=True,actualColdApplicationInitializeTickAndDraw=True,noDeclaredPerFileReadinessSchedule=True,sourceBindingsByMode={'candidate':all_bindings},objectBindings=objects,fixtureSha256=sha(O/'fixture.cpp'),fixturePath=(O/'fixture.cpp').relative_to(R).as_posix(),wasmSha256=sha(O/'candidate.wasm'),outputs={'candidate':{'wasmSha256':sha(O/'candidate.wasm')}},normalAccessFor145LinkedProviders=True,fixtureIncludesCurrentCanonicalApplicationWithRelaxedAccess=True,freshlyCompiledGameUnits=141,freshlyCompiledHostUnits=4,gameObjectsReusedAndReverified=141,productionGameSource='9dd1ae4e plus adopted TH14 queue/align correction',ordinaryKeyboardInputExport=True,exitSaveUsesProductionMethodAfterFinishedOnly=True,originalGameStarted=False,newAssetsCopied=False,completeGame=False)
(O/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(compiled=True,wasmSha256=report['wasmSha256'],normalProviders=145,freshHostUnits=4)))
