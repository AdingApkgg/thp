"""Build a quiet ordinary Application probe with141+4 fresh normal providers."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/player-initialization-oracle-nov13';O=H/'application/component';O.mkdir(parents=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
core=load(H/'candidate-providers/build.json');S=R/core['sourceSnapshotRoot']
for name,digest in core['sourceBindings'].items():assert sha(S/name)==sha(R/name)==digest,name
for row in core['currentProviders']:assert sha(R/row['object'])==row['objectSha256']
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==core['compilerSha256']
flags=core['flags']+['-D__EMSCRIPTEN__=1','-I'+str(S/'runtimes/th12/th12_web/cpp/sdl'),'-I'+str(S/'runtimes/th12/portable/sdl'),'-I'+str(R/'artifacts/th14/boot-main-intake-nov07/application-component/include')]
env=dict(os.environ,TEMP=str(O),TMP=str(O),TMPDIR=str(O));objects={x['object']:x['objectSha256']for x in core['currentProviders']}
for name in ['th12_web/cpp/sdl/AudioDevice.cpp','th12_web/cpp/sdl/FontDevice.cpp','th12_web/cpp/sdl/GraphicsDevice.cpp','portable/sdl/Renderer.cpp']:
 source=S/'runtimes/th12'/name;obj=O/(source.name+'.o');unit_flags=[f for f in flags if f!='-D__EMSCRIPTEN__=1']if source.name=='AudioDevice.cpp'else flags
 command=[str(cc),*unit_flags,'-c',str(source),'-o',str(obj)]
 with obj.with_suffix('.log').open('wb')as log:subprocess.run(command,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
 objects[obj.relative_to(R).as_posix()]=sha(obj)
prior=R/'artifacts/th14/helper-clear-oracle-nov13/application/component';base=load(prior/'build.json')
assert sha(prior/'fixture.cpp')==base['fixtureSha256']
for name in ['fixture.cpp','Th14WarmAttractCase.hpp']:(O/name).write_bytes((prior/name).read_bytes())
cmd=[str(cc),*flags,'-fno-access-control','-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(O/'fixture.cpp'),*[str(R/n)for n in objects],'-o',str(O/'candidate.wasm')]
with(O/'link.log').open('wb')as log:subprocess.run(cmd,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
bindings={(S/n).relative_to(R).as_posix():h for n,h in core['sourceBindings'].items()}
for p in [Path(__file__),O/'fixture.cpp',O/'Th14WarmAttractCase.hpp',R/'runtimes/th12/th12_web/tests/cpp/th14-native-title-live-observer.hpp']:bindings[p.relative_to(R).as_posix()]=sha(p)
report=dict(base,sourceBindings=bindings,sourceBindingsByMode={'candidate':bindings},objectBindings=objects,
            sourceRoot=str(S),fixturePath=(O/'fixture.cpp').relative_to(R).as_posix(),fixtureSha256=sha(O/'fixture.cpp'),
            wasmSha256=sha(O/'candidate.wasm'),normalProviders=145,freshNormalGameUnits=141,freshNormalHostUnits=4,
            fixtureOnlyRelaxedAccess=True,command=cmd,gameSourceBase='84b8741af5b7ca617cc4046fe697d3cbfebbf4ad',completeGame=False)
(O/'build.json').write_text(json.dumps(report,indent=2)+'\n')
driver=(R/'tools/th14-run-upstream-helper-start-nov13.mjs').read_text()
old='artifacts/th14/upstream-helper-integration-nov12/application-production';assert driver.count(old)==1
driver=driver.replace(old,'artifacts/th14/player-initialization-oracle-nov13/application')
path=R/'tools/th14-run-null-rate-ordinary-start-nov13.mjs';assert not path.exists();path.write_text(driver,encoding='utf8',newline='\n')
print(json.dumps(dict(wasmSha256=report['wasmSha256'],freshNormalProviders=145,driverSha256=sha(path))))
