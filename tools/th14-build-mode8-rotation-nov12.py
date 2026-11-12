"""Link current ordinary providers to both mode8 matrix and actual renderer branches."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/mode8-rotation-nov12';O=H/'component';O.mkdir(exist_ok=False);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
b=load(R/'artifacts/th14/camera-roles-nov12-v3/current-provider-bindings.json')
for p,d in b['sourceBindings'].items():assert sha(R/p)==d,p
for row in b['currentProviders']:assert sha(Path(row['object']))==row['objectSha256']
base=R/'tools/th14-mode8-display-component-nov12.cpp';code=base.read_text().replace('\r\n','\n');anchor=' v.script_position={f(r[0x3c/4]),f(r[0x40/4]),f(r[0x44/4])};';assert code.count(anchor)==1;code=code.replace(anchor,anchor+'\n v.rotation={f(r[0x48/4]),f(r[0x4c/4]),f(r[0x50/4])};')
matrix=O/'matrix-derived.cpp';matrix.write_text(code,encoding='utf8',newline='\n');parent=R/'tools/th14-mode8-display-renderer-component-nov12.cpp';code=parent.read_text().replace('"th14-mode8-display-component-nov12.cpp"','"matrix-derived.cpp"');fixture=O/'renderer-derived.cpp';fixture.write_text(code,encoding='utf8',newline='\n')
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==b['compilerSha256'];flags=b['flags']+['-DTH14_MODE8_SPACE_CANDIDATE=1'];cmd=[str(cc),*flags,'-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(fixture),*[r['object'] for r in b['currentProviders']],'-o',str(O/'probe.wasm')]
with (O/'link.log').open('wb') as log:subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120,env={**os.environ,'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)})
report=dict(normalProviderAccess=True,actualCurrentAnmProjectionAndRenderer=True,sourceBindings=b['sourceBindings'],semanticNoOpSourceRebindings=b['semanticNoOpSourceRebindings'],objectBindings={r['object']:r['objectSha256'] for r in b['currentProviders']},fixtureParentBindings={str(p.relative_to(R)).replace('\\','/'):sha(p) for p in [base,parent]},fixtureSha256=sha(fixture),matrixFixtureSha256=sha(matrix),wasmSha256=sha(O/'probe.wasm'),completeGame=False)
(O/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['sourceBindings','objectBindings','fixtureParentBindings','semanticNoOpSourceRebindings']}))
