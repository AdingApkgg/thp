"""Freeze current sources and rebuild every normal game provider for Timer.hpp."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,os,subprocess,time
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/player-initialization-oracle-nov13';O=H/'candidate-providers'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
O.mkdir();S=O/'source';objects=O/'objects';objects.mkdir()
parent_path=R/'artifacts/th14/loading-control4-nov13/provider/build.json';parent=json.loads(parent_path.read_bytes())
edits=json.loads((H/'candidate-edits.json').read_bytes());changed={r['path']for r in edits['files']}
bindings={n:sha(R/n)for n in parent['sourceBindings']}
assert {n for n,h in bindings.items()if h!=parent['sourceBindings'][n]}==changed
for name in bindings:
 source=R/name;target=S/name;target.parent.mkdir(parents=True,exist_ok=True)
 if name in changed:target.write_bytes(source.read_bytes())
 else:os.link(source,target)
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==parent['compilerSha256']
flags=[f for f in parent['flags']if not f.startswith('-I')]+['-I'+str(S/'runtimes/th12/th12_web/cpp/game')]
assert '-fno-access-control'not in flags
env=dict(os.environ,TEMP=str(O),TMP=str(O),TMPDIR=str(O));began=time.monotonic()
def compile(row):
 source=S/row['source'];obj=objects/(source.name+'.o');command=[str(cc),*flags,'-c',str(source),'-o',str(obj)]
 with obj.with_suffix('.log').open('wb')as log:subprocess.run(command,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
 return dict(source=row['source'],sourceSha256=sha(source),compiledSource=source.relative_to(R).as_posix(),object=obj.relative_to(R).as_posix(),objectSha256=sha(obj))
with ThreadPoolExecutor(max_workers=3)as pool:providers=list(pool.map(compile,parent['currentProviders']))
for n,h in bindings.items():assert sha(R/n)==sha(S/n)==h,n
report=dict(parent,sourceBindings=bindings,flags=flags,currentProviders=providers,normalEngineAccessControl=True,
            sourceSnapshotRoot=S.relative_to(R).as_posix(),gameUnitsCompiled=len(providers),gameObjectsReused=0,
            all141FreshForCurrentSource=True,all141VerifiedReusedForUnchangedGameSources=False,
            currentSourceChanges=sorted(changed),parentProviderBuildSha256=sha(parent_path),
            toolSha256=sha(Path(__file__)),elapsedSeconds=time.monotonic()-began,completeGame=False)
report.pop('providerDerivation',None);report.pop('nonGameImplementationOnlyChangesSinceCompilation',None)
(O/'build.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(gameUnitsCompiled=len(providers),normalEngineAccessControl=True,elapsedSeconds=report['elapsedSeconds'])),flush=True)
