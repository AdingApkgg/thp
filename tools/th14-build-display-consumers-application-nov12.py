"""Relink the actual Application with the qualified normal consumer providers."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/display-consumers-nov12';P=R/'artifacts/th14/display-mode-entry-nov12'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
B=load(H/'component/build.json');S=Path(B['sourceRoot']);base=load(P/'application/component/build.json');provider=load(H/'current-provider-bindings.json')
O=H/'application/component';O.mkdir(parents=True,exist_ok=False)
for name,digest in B['sourceBindings'].items():assert sha(S/name)==digest,name
objects={r['object']:r['objectSha256'] for r in B['currentProviders']};objects.update(provider['normalHostObjectBindings'])
for name,digest in objects.items():assert sha(R/name)==digest,name
assert len(objects)==145
for name in ('fixture.cpp','Th14WarmAttractCase.hpp'):(O/name).write_bytes((P/'application/component'/name).read_bytes())
flags=B['flags']+['-I'+str(S/'runtimes/th12/th12_web/cpp/sdl'),'-I'+str(S/'runtimes/th12/portable/sdl'),'-I'+str(R/'artifacts/th14/boot-main-intake-nov07/application-component/include')]
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==B['compilerSha256']
with (O/'link.log').open('wb') as log:
    subprocess.run([str(cc),*flags,'-fno-access-control','-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(O/'fixture.cpp'),*[str(R/n) for n in objects],'-o',str(O/'candidate.wasm')],cwd=R,stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)},check=True,timeout=180)
bindings={(S/n).relative_to(R).as_posix():d for n,d in B['sourceBindings'].items()}
for p in (O/'fixture.cpp',O/'Th14WarmAttractCase.hpp',R/'runtimes/th12/th12_web/tests/cpp/th14-native-title-live-observer.hpp'):bindings[p.relative_to(R).as_posix()]=sha(p)
report={**base,'sourceRoot':str(S),'sourceBindings':bindings,'sourceBindingsByMode':{'candidate':bindings},'objectBindings':objects,'wasmSha256':sha(O/'candidate.wasm'),'fixtureSha256':sha(O/'fixture.cpp'),'fixturePath':(O/'fixture.cpp').relative_to(R).as_posix(),'normalProviders':145,'completeGame':False}
(O/'build.json').write_text(json.dumps(report,indent=2)+'\n')
driver=R/'tools/th14-run-display-mode-title-quit-nov12.mjs';text=driver.read_text(encoding='utf8')
assert text.count("home=resolve(root,'artifacts/th14/display-mode-entry-nov12/application')")==1
text=text.replace("home=resolve(root,'artifacts/th14/display-mode-entry-nov12/application')","home=resolve(root,'artifacts/th14/display-consumers-nov12/application')")
out=R/'tools/th14-run-display-consumers-title-quit-nov12.mjs';assert not out.exists();out.write_text(text,encoding='utf8',newline='')
(H/'application/driver-binding.json').write_text(json.dumps(dict(parent=driver.relative_to(R).as_posix(),parentSha256=sha(driver),derived=out.relative_to(R).as_posix(),derivedSha256=sha(out),onlyHomeChanged=True),indent=2)+'\n')
print(json.dumps(dict(wasmSha256=report['wasmSha256'],normalProviders=145,fixtureOnlyRelaxedAccess=True)))
