"""Link a repaint diagnostic onto current verified Application providers."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/current-first-present-uv-repaint-nov12'
O=H/'component'
B=R/'artifacts/th14/control-main-stop-nov12/first-present/probe-v2'
P=R/'artifacts/th14/current-low-pause-pixels-nov12/component'
C=R/'artifacts/th14/control-main-stop-nov12/current-core'
load=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not H.exists()
parent,old,core=load(P/'build.json'),load(B/'candidate/build.json'),load(C/'build.json')
assert parent['objectBindings']==old['objectBindings']
for meta in [parent,old]:
 for p,h in {**meta['sourceBindingsByMode']['candidate'],**meta['objectBindings']}.items():assert sha(R/p)==h,p
assert sha(B/'fixture.cpp')==old['fixtureSha256']
O.mkdir(parents=True)
source=(B/'fixture.cpp').read_text(encoding='utf8')+'\n'+(R/'tools/th14-first-present-uv-repaint-nov12.inc.cpp').read_text(encoding='utf8')
(O/'fixture.cpp').write_text(source,encoding='utf8',newline='\n')
for name in ['Application.cpp','InitialCppResourcesTh14.hpp','Th14WarmAttractCase.hpp']:(O/name).write_bytes((B/name).read_bytes())
rt=R/'runtimes/th12';cc=rt/'tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
assert sha(cc)==core['compilerSha256']
flags=core['flags']+['-I'+str(rt/'th12_web/cpp/sdl'),'-I'+str(rt/'portable/sdl'),'-I'+str(R/'artifacts/th14/boot-main-intake-nov07/application-component/include')]
cmd=[str(cc),*flags,'-fno-access-control','-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined',
 '-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(O/'fixture.cpp'),
 *[str(R/p) for p in parent['objectBindings']],'-o',str(O/'candidate.wasm')]
(O/'command.json').write_text(json.dumps(cmd,indent=2)+'\n')
with (O/'compile.log').open('wb') as f:
 result=subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=240,env={**os.environ,'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)})
assert result.returncode==0,(O/'compile.log').read_text(errors='replace')[-4000:]
bindings={p:h for p,h in parent['sourceBindingsByMode']['candidate'].items()}
for p in [Path(__file__),R/'tools/th14-first-present-uv-repaint-nov12.inc.cpp',O/'fixture.cpp',*[O/n for n in ['Application.cpp','InitialCppResourcesTh14.hpp','Th14WarmAttractCase.hpp']]]:bindings[p.relative_to(R).as_posix()]=sha(p)
report=dict(actualColdApplicationInitializeTickAndDraw=True,noDeclaredPerFileReadinessSchedule=True,
 sourceBindingsByMode={'candidate':bindings},objectBindings=parent['objectBindings'],fixturePath=(O/'fixture.cpp').relative_to(R).as_posix(),fixtureSha256=sha(O/'fixture.cpp'),
 wasmSha256=sha(O/'candidate.wasm'),outputs={'candidate':{'wasmSha256':sha(O/'candidate.wasm')}},
 frozenCurrentApplicationWithExistingReadObservers=True,newDiagnosticRepaintOnly=True,
 parentObservedApplicationBuildSha256=sha(B/'candidate/build.json'),parentNormalProviderBuildSha256=sha(P/'build.json'),
 gameObjectsReusedAndReverified=141,hostObjectsReusedAndReverified=4,normalProviderAccessControl=True,fixtureOnlyRelaxedAccess=True,
 observationStride=49,productionGameSource=parent['productionGameSource'],productionChanged=False,completeGame=False)
(O/'build.json').write_text(json.dumps(report,indent=2)+'\n')
(O/'actual-link-object-bindings.json').write_text(json.dumps(dict(actualLinkObjectBindings=parent['objectBindings']),indent=2)+'\n')
print(json.dumps(dict(compiled=True,wasmSha256=report['wasmSha256'],providers=145)))
