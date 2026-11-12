"""Quiet real Application probe using the fresh candidate ABI and normal providers."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/camera-right-pair-nov12';O=H/'application/component';O.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
core=load(H/'candidate/build.json');S=Path(core['sourceRoot']);B=R/'artifacts/th14/mode8-display-space-nov12/application/component';prior=load(B/'build.json')
for p,d in core['sourceBindings'].items():assert sha(S/p)==d,p
assert sha(B/'fixture.cpp')==prior['fixtureSha256']
strip_includes=lambda s:'\n'.join(x for x in s.replace('\r\n','\n').splitlines() if not x.lstrip().startswith('#include'))
actual=S/'runtimes/th12/th12_web/cpp/sdl/Application.cpp';observed=(B/'Application.cpp').read_text();assert strip_includes(actual.read_text())==strip_includes(observed)
observed=observed.replace('H:/code/thp/runtimes/',(S/'runtimes').as_posix()+'/');(O/'Application.cpp').write_text(observed,encoding='utf8',newline='\n')
for name in ['InitialCppResourcesTh14.hpp','Th14WarmAttractCase.hpp','fixture.cpp']:(O/name).write_bytes((B/name).read_bytes())
fixture=O/'fixture.cpp';code=fixture.read_text();code+='\nAPI(world_right_alignment) th11::u32 world_right_alignment(){return current?th11::u32(reinterpret_cast<std::uintptr_t>(&current->session.compositor.world_camera.right)&7u):0xffffffffu;}\n';fixture.write_text(code,encoding='utf8',newline='\n')
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==core['compilerSha256']
rt=S/'runtimes/th12';flags=core['flags']+['-I'+str(rt/'th12_web/cpp/sdl'),'-I'+str(rt/'portable/sdl'),'-I'+str(R/'artifacts/th14/boot-main-intake-nov07/application-component/include')]
objects={r['object']:r['objectSha256'] for r in core['objects']};env={**os.environ,'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)}
for name in ['th12_web/cpp/sdl/AudioDevice.cpp','th12_web/cpp/sdl/FontDevice.cpp','th12_web/cpp/sdl/GraphicsDevice.cpp','portable/sdl/Renderer.cpp']:
    source=rt/name;obj=O/(source.name+'.o')
    with (O/(source.name+'.log')).open('wb') as log:subprocess.run([str(cc),*flags,'-c',str(source),'-o',str(obj)],cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120,env=env)
    objects[obj.relative_to(R).as_posix()]=sha(obj)
for p,d in objects.items():assert sha(R/p)==d,p
cmd=[str(cc),*flags,'-fno-access-control','-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(fixture),*[str(R/p) for p in objects],'-o',str(O/'candidate.wasm')]
with (O/'link.log').open('wb') as log:subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180,env=env)
bindings={(S/p).relative_to(R).as_posix():d for p,d in core['sourceBindings'].items()}
for p in [O/n for n in ['Application.cpp','InitialCppResourcesTh14.hpp','Th14WarmAttractCase.hpp','fixture.cpp']]+[R/'runtimes/th12/th12_web/tests/cpp/th14-native-title-live-observer.hpp']:bindings[p.relative_to(R).as_posix()]=sha(p)
report=dict(actualColdApplicationInitializeTickAndDraw=True,noDeclaredPerFileReadinessSchedule=True,sourceBindingsByMode={'candidate':bindings},objectBindings=objects,fixturePath=fixture.relative_to(R).as_posix(),fixtureSha256=sha(fixture),wasmSha256=sha(O/'candidate.wasm'),outputs={'candidate':{'wasmSha256':sha(O/'candidate.wasm')}},freshNormalGameUnits=141,freshNormalHostUnits=4,fixtureOnlyRelaxedAccess=True,canonicalApplicationBodyByteMatchIgnoringIncludes=True,existingReadOnlyShtObserversRetained=True,completeGame=False)
(O/'build.json').write_text(json.dumps(report,indent=2)+'\n');(O/'actual-link-object-bindings.json').write_text(json.dumps({'actualLinkObjectBindings':objects},indent=2)+'\n')
driver=(R/'tools/th14-run-mode8-display-application-nov12.mjs').read_text();old='artifacts/th14/mode8-display-space-nov12/application';assert driver.count(old)==1;driver=driver.replace(old,'artifacts/th14/camera-right-pair-nov12/application')
old=" assert.equal(platform.getError(),0,'GPU initialization');phase='application-frames';";assert driver.count(old)==1;driver=driver.replace(old," assert.equal(c.world_right_alignment(),0,'Shared world-camera qword alignment');\n"+old)
old=' boundedDiagnosticOnly:true,actualColdApplication:true';assert driver.count(old)==1;driver=driver.replace(old,' sharedWorldRightQwordAlignedAtRealApplicationStart:true,publicationCandidateNotYetAdopted:true,\n'+old)
p=R/'tools/th14-run-camera-right-pair-application-nov12.mjs';assert not p.exists();p.write_text(driver,encoding='utf8',newline='\n')
print(json.dumps(dict(normalProviders=145,wasmSha256=report['wasmSha256'],driverSha256=sha(p))))
