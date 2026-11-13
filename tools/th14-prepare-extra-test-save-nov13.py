"""Build an explicit unlocked external save fixture through production codecs."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];O=R/'artifacts/th14/behavior-matrix-nov13/extra-save-input';O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
b=load(R/'artifacts/th14/alpha-range-current-nov13/current-provider-bindings.json')
for n,h in {**b['sourceBindings'],**b['objectBindings']}.items():assert sha(R/n)==h,n
meta=load(R/'artifacts/th14/option-refresh-oracle-nov13/candidate-providers/build.json');cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==meta['compilerSha256']
flags=['-I'+str(R/'runtimes/th12/th12_web/cpp/game')if x.startswith('-I')else x for x in meta['flags']]
fixture=R/'tools/th14-extra-unlock-save-nov13.cpp';cmd=[str(cc),*flags,'-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(fixture),*[str(R/n)for n in b['objectBindings']],'-o',str(O/'save-fixture.wasm')]
assert '-fno-access-control'not in cmd
with(O/'build.log').open('wb')as f:q=subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=180,env=dict(os.environ,TEMP=str(O),TMP=str(O),TMPDIR=str(O)))
assert q.returncode==0,(O/'build.log').read_text(errors='replace')[-2000:]
(O/'build.json').write_text(json.dumps(dict(fixtureSha256=sha(fixture),wasmSha256=sha(O/'save-fixture.wasm'),normalAccess=True,productionObjectsVerified=141,externalControlledSavePrecondition=True,unlockEarnedThroughOrdinaryPlayAccepted=False,noLiveGameMemoryOrRealUserSaveModified=True,completeGame=False),indent=2)+'\n');print('Built explicit external Extra-unlock save fixture')
