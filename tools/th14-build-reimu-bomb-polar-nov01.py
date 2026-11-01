"""Link the real damage and bomb producers against a fully compiled core."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--core-build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
B=a.core_build.resolve(strict=True);O=a.output.resolve();assert B.is_relative_to(R/'artifacts/th14')and O.is_relative_to(R/'artifacts/th14')and not O.exists();O.mkdir()
b=json.loads(B.read_bytes());assert len(b['objectBindings'])==141
for row in b['objectBindings']:assert SHA(Path(row['path']).read_bytes())==row['sha256']
fixture=R/'runtimes/th12/th12_web/tests/cpp/th14-reimu-bomb-polar-nov01.cpp';compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
assert SHA(compiler.read_bytes())==b['compilerSha256']
run=subprocess.run([str(compiler),*b['flags'],*b['linkFlags'],str(fixture),*[x['path']for x in b['objectBindings']],'-o',str(O/'stack.wasm')],capture_output=True,env=dict(os.environ,TEMP=str(O),TMP=str(O)))
(O/'link.log').write_bytes(run.stdout+run.stderr);assert run.returncode==0,run.stderr.decode(errors='replace')[-2500:]
report=dict(wasmSha256=SHA((O/'stack.wasm').read_bytes()),coreBuild=B.relative_to(R).as_posix(),coreBuildSha256=SHA(B.read_bytes()),fixture=fixture.relative_to(R).as_posix(),fixtureSha256=SHA(fixture.read_bytes()),compilerSha256=b['compilerSha256'],toolSha256=SHA(Path(__file__).read_bytes()),referenceCollectorEntryAlignment=4,liveValuesSuppliedToEngine=False,completeGame=False,nativeEquivalent=False)
(O/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
