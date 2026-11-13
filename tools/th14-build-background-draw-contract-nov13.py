from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];O=R/'artifacts/th14/background-draw-contract-v2-nov13'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
p=load(R/'artifacts/th14/compositor-filter-nov13/current-provider-bindings.json')
for n,h in {**p['sourceBindings'],**p['objectBindings']}.items():assert sha(R/n)==h,n
provider=load(R/'artifacts/th14/option-refresh-oracle-nov13/candidate-providers/build.json')
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==provider['compilerSha256']
flags=[('-I'+str(R/'runtimes/th12/th12_web/cpp/game')) if x.startswith('-I')and x.replace('\\','/').endswith('/cpp/game')else x for x in provider['flags']]
fixture=R/'tools/th14-background-draw-contract-nov13.cpp';wasm=O/'current.wasm';assert not wasm.exists()
cmd=[str(cc),*flags,'-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(fixture),*[str(R/n)for n in p['objectBindings']],'-o',str(wasm)]
with(O/'compile.log').open('wb')as f:q=subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=180,env=dict(os.environ,TEMP=str(O),TMP=str(O),TMPDIR=str(O)))
assert q.returncode==0,(O/'compile.log').read_text(errors='replace')[-3000:]
(O/'build.json').write_text(json.dumps(dict(sourceBindings=p['sourceBindings'],objectBindings=p['objectBindings'],fixtureSha256=sha(fixture),wasmSha256=sha(wasm),compilerSha256=sha(cc),normalAccess=True,completeGame=False),indent=2)+'\n')
print('Linked current background fixture with 141 verified normal providers')
