"""Link current normal providers to the real threaded camera-owner fixture."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/camera-copy-constructor-nov13';O=H/'component-v2';O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
P=R/'artifacts/th14/option-refresh-oracle-nov13/candidate-providers/build.json';b=json.loads(P.read_bytes())
for name,digest in b['sourceBindings'].items():assert sha(R/name)==digest,name
objects={r['object']:r['objectSha256']for r in b['currentProviders']};assert len(objects)==141
for name,digest in objects.items():assert sha(R/name)==digest,name
fixture=R/'tools/th14-camera-copy-constructor-nov13.cpp';(O/'fixture.cpp').write_bytes(fixture.read_bytes())
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==b['compilerSha256']
cmd=[str(cc),*b['flags'],'-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined',
 '-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(O/'fixture.cpp'),*[str(R/n)for n in objects],'-o',str(O/'probe.wasm')]
assert '-fno-access-control'not in cmd
with(O/'build.log').open('wb')as log:result=subprocess.run(cmd,cwd=R,env=dict(os.environ,TEMP=str(O),TMP=str(O),TMPDIR=str(O)),stdout=log,stderr=subprocess.STDOUT,timeout=180)
assert result.returncode==0,(O/'build.log').read_text(errors='replace')[-3000:]
report=dict(sourceCommit='59a8cc4cc5ae404d8439019b35f4915f75c03c5d',normalAccessControl=True,gameObjectsVerifiedReused=141,
 wasmSha256=sha(O/'probe.wasm'),fixtureSha256=sha(O/'fixture.cpp'),sourceBindings=b['sourceBindings'],objectBindings=objects,
 providerBuildSha256=sha(P),command=cmd,toolSha256=sha(Path(__file__)),completeGame=False)
(O/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(compiled=True,wasmSha256=report['wasmSha256'])))
