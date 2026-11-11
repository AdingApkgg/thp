"""Link current normal providers for one stopped first-Present GPU check."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/first-present-alpha-localization-nov12/batch-state';O=H/'application/component';assert not O.exists();O.mkdir(parents=True);load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();q=load(H/'qualified.json');assert q['sourceAdopted'];core=load(R/'artifacts/th14/mode8-display-space-nov12/current-core/build.json');parent=load(R/'artifacts/th14/mode8-display-space-nov12/application/component/build.json');B=R/'artifacts/th14/control-main-stop-nov12/first-present/probe-v2';prior=load(B/'candidate/build.json');normal=load(H/'candidate/build.json');renderer='runtimes/th12/th12_web/cpp/game/AnmRenderer.cpp'
bindings={p:sha(R/p)for p in core['sourceBindings']};assert {p for p in bindings if bindings[p]!=core['sourceBindings'][p]}=={renderer};assert bindings[renderer]==q['sourceAfterSha256'];assert sha(B/'fixture.cpp')==prior['fixtureSha256'];objects=dict(normal['objects']);assert len(objects)==141
for p,d in parent['objectBindings'].items():
 if p.endswith('/AnmRenderer.cpp.o')or '/current-core/objects/'in p:continue
 assert sha(R/p)==d;objects[p]=d
assert len(objects)==145
for p,d in objects.items():assert sha(R/p)==d,p
for name in ['Application.cpp','InitialCppResourcesTh14.hpp','Th14WarmAttractCase.hpp']:(O/name).write_bytes((B/name).read_bytes());bindings[(O/name).relative_to(R).as_posix()]=sha(O/name)
fixture=(B/'fixture.cpp').read_text()+'\n'+(R/'tools/th14-first-present-uv-repaint-nov12.inc.cpp').read_text();(O/'fixture.cpp').write_text(fixture,encoding='utf8',newline='\n');bindings[(O/'fixture.cpp').relative_to(R).as_posix()]=sha(O/'fixture.cpp');bindings['tools/th14-first-present-uv-repaint-nov12.inc.cpp']=sha(R/'tools/th14-first-present-uv-repaint-nov12.inc.cpp')
for p,d in parent['sourceBindingsByMode']['candidate'].items():
 if p.startswith('artifacts/'):continue
 if p!=renderer:assert sha(R/p)==d,p
 bindings[p]=sha(R/p)
rt=R/'runtimes/th12';cc=rt/'tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==core['compilerSha256'];flags=core['flags']+['-I'+str(rt/'th12_web/cpp/sdl'),'-I'+str(rt/'portable/sdl'),'-I'+str(R/'artifacts/th14/boot-main-intake-nov07/application-component/include')];cmd=[str(cc),*flags,'-fno-access-control','-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(O/'fixture.cpp'),*[str(R/p)for p in objects],'-o',str(O/'candidate.wasm')]
with(O/'compile.log').open('wb')as f:subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=180,env={**os.environ,'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)})
report=dict(actualColdApplicationInitializeTickAndDraw=True,noDeclaredPerFileReadinessSchedule=True,sourceBindingsByMode={'candidate':bindings},objectBindings=objects,fixturePath=(O/'fixture.cpp').relative_to(R).as_posix(),fixtureSha256=sha(O/'fixture.cpp'),wasmSha256=sha(O/'candidate.wasm'),outputs={'candidate':{'wasmSha256':sha(O/'candidate.wasm')}},frozenCurrentApplicationWithExistingReadObservers=True,gameObjectsReusedAndReverified=141,hostObjectsReusedAndReverified=4,normalProviderAccessControl=True,fixtureOnlyRelaxedAccess=True,observationStride=49,productionChanged=True,productionGameSource='28d36fe8 plus adopted type0 batch-order fix',completeGame=False)
(O/'build.json').write_text(json.dumps(report,indent=2)+'\n');(O/'actual-link-object-bindings.json').write_text(json.dumps(dict(actualLinkObjectBindings=objects),indent=2)+'\n');print(json.dumps(dict(compiled=True,wasmSha256=report['wasmSha256'],providers=145)))
