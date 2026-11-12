from pathlib import Path
import hashlib,json,subprocess,os
R=Path(__file__).resolve().parents[1];O=R/'artifacts/th14/replay-save-reopen-nov13'
assert not O.exists();O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
parent=load(R/'artifacts/th14/replay-entry-flag-nov13/current-provider-bindings.json')
for p,h in {**parent['sourceBindings'],**parent['objectBindings']}.items():assert sha(R/p)==h,p
provider=load(R/'artifacts/th14/option-refresh-oracle-nov13/candidate-providers/build.json')
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==provider['compilerSha256']
fixture=R/'tools/th14-replay-save-reopen-nov13.cpp';wasm=O/'probe.wasm'
cmd=[str(cc),*provider['flags'],'-fno-access-control','-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(fixture),*[str(R/p)for p in parent['objectBindings']],'-o',str(wasm)]
with(O/'build.log').open('wb')as f:q=subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=180,env=dict(os.environ,TEMP=str(O),TMP=str(O),TMPDIR=str(O)))
assert q.returncode==0,(O/'build.log').read_text(errors='replace')[-3000:]
(O/'build.json').write_text(json.dumps(dict(sourceBindings=parent['sourceBindings'],objectBindings=parent['objectBindings'],normalProductionProviders=141,
 fixtureOnlyRelaxedAccess=True,fixtureSha256=sha(fixture),wasmSha256=sha(wasm),productionChanged=False,completeGame=False),indent=2)+'\n')
print('Linked 141 verified current providers to actual session save/reopen probe.')
