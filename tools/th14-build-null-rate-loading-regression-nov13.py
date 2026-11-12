"""Relink the corrected owner-lifetime loading fixture with fresh providers."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/player-initialization-oracle-nov13';O=H/'loading-component';O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();provider_path=H/'candidate-providers/build.json';provider=json.loads(provider_path.read_bytes())
for name,digest in provider['sourceBindings'].items():assert sha(R/name)==digest,name
for row in provider['currentProviders']:assert sha(R/row['object'])==row['objectSha256']
prior=R/'artifacts/th14/loading-control4-nov13/scoped-owner';baseline=json.loads((prior/'build.json').read_bytes())
assert sha(prior/'fixture.cpp')==baseline['observerBindings'][(prior/'fixture.cpp').relative_to(R).as_posix()]
fixture=O/'fixture.cpp';fixture.write_bytes((prior/'fixture.cpp').read_bytes())
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==provider['compilerSha256']
cmd=[str(cc),*provider['flags'],'-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(fixture),*[row['object']for row in provider['currentProviders']],'-o',str(O/'probe.wasm')]
assert '-fno-access-control'not in cmd
with(O/'build.log').open('wb')as log:subprocess.run(cmd,cwd=R,env=dict(os.environ,TEMP=str(O),TMP=str(O),TMPDIR=str(O)),stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
report=dict(providerBuild=str(provider_path),providerBuildSha256=sha(provider_path),sourceBindings=provider['sourceBindings'],
            observerBindings={p.relative_to(R).as_posix():sha(p)for p in [Path(__file__),fixture,prior/'fixture.cpp']},
            wasmSha256=sha(O/'probe.wasm'),command=cmd,fixtureNormalAccessControl=True,privateRegistryAccess=False,
            templateOwnerLifetimeCorrect=True,all141ProvidersFresh=True,completeGame=False)
(O/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(wasmSha256=report['wasmSha256'])))
