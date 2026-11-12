"""Recompile only the changed PlayerFrame provider; preserve all141 bindings."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/option-refresh-oracle-nov13';P=R/'artifacts/th14/player-initialization-oracle-nov13'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
parent_path=P/'candidate-providers/build.json';parent=load(parent_path);edit=load(H/'candidate-edits.json');O=H/'candidate-providers';O.mkdir();S=O/'source';(O/'objects').mkdir()
bindings={n:sha(R/n)for n in parent['sourceBindings']};assert {n for n,h in bindings.items()if h!=parent['sourceBindings'][n]}=={edit['path']}
for name in bindings:
 source=R/name;target=S/name;target.parent.mkdir(parents=True,exist_ok=True)
 if name==edit['path']:target.write_bytes(source.read_bytes())
 else:os.link(source,target)
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==parent['compilerSha256']
flags=[f for f in parent['flags']if not f.startswith('-I')]+['-I'+str(S/'runtimes/th12/th12_web/cpp/game')]
env=dict(os.environ,TEMP=str(O),TMP=str(O),TMPDIR=str(O));providers=[]
for row in parent['currentProviders']:
 assert sha(R/row['object'])==row['objectSha256'];current=dict(row)
 if row['source']==edit['path']:
  source=S/row['source'];obj=O/'objects/PlayerFrame.cpp.o';cmd=[str(cc),*flags,'-c',str(source),'-o',str(obj)]
  with(O/'compile.log').open('wb')as log:subprocess.run(cmd,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
  current.update(sourceSha256=sha(source),compiledSource=source.relative_to(R).as_posix(),object=obj.relative_to(R).as_posix(),objectSha256=sha(obj))
 providers.append(current)
report=dict(parent,currentProviders=providers,sourceBindings=bindings,sourceSnapshotRoot=S.relative_to(R).as_posix(),flags=flags,
            gameUnitsCompiled=1,gameObjectsReused=140,all141FreshForCurrentSource=False,all141HaveCurrentSourceAndHeaderBindings=True,
            currentSourceChanges=[edit['path']],parentProviderBuildSha256=sha(parent_path),toolSha256=sha(Path(__file__)),completeGame=False)
(O/'build.json').write_text(json.dumps(report,indent=2)+'\n')
C=H/'candidate-component';C.mkdir();prior=load(H/'component/build.json');assert sha(H/'component/fixture.cpp')==prior['observerBindings'][(H/'component/fixture.cpp').relative_to(R).as_posix()]
fixture=C/'fixture.cpp';fixture.write_bytes((H/'component/fixture.cpp').read_bytes())
cmd=[str(cc),*flags,'-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(fixture),*[r['object']for r in providers],'-o',str(C/'probe.wasm')]
assert '-fno-access-control'not in cmd
with(C/'build.log').open('wb')as log:subprocess.run(cmd,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
component=dict(prior,sourceBindings=bindings,objectBindings={r['object']:r['objectSha256']for r in providers},
 observerBindings={p.relative_to(R).as_posix():sha(p)for p in [Path(__file__),fixture,H/'component/fixture.cpp']},
 providerBuild=str(O/'build.json'),providerBuildSha256=sha(O/'build.json'),gameObjectsReused=140,gameUnitsRecompiled=1,
 wasmSha256=sha(C/'probe.wasm'),gameSourceBase=prior['gameSource'],gameSource=None,command=cmd,completeGame=False)
(C/'build.json').write_text(json.dumps(component,indent=2)+'\n')
driver=(R/'tools/th14-run-option-refresh-oracle-nov13.mjs').read_text().replace("'component/build.json'","'candidate-component/build.json'").replace("'component/probe.wasm'","'candidate-component/probe.wasm'").replace("'result.json'","'candidate-result.json'")
path=R/'tools/th14-run-option-initial-state-candidate-nov13.mjs';assert not path.exists();path.write_text(driver,encoding='utf8',newline='\n')
print(json.dumps(dict(wasmSha256=component['wasmSha256'],gameUnitsRecompiled=1,gameObjectsVerifiedReused=140)))
