"""Build a small production-header component, without touching engine objects."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess
R=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')and not out.exists()
out.mkdir(parents=True)
assert shutil.disk_usage(out).free>=100*1024**3,'Preserve 100 GiB free space'
source=R/'runtimes/th12/th12_web/cpp/game';headers={}
for name in ['Types.hpp','PortTitle.hpp','Rng.hpp','ReplayRngRestoreTh14.hpp']:
    raw=(source/name).read_bytes();(out/name).write_bytes(raw);headers[name]=SHA(raw)
fixture=R/'runtimes/th12/th12_web/tests/cpp/th14-independent-rng-delivery-nov05.cpp'
raw=fixture.read_bytes();(out/'fixture.cpp').write_bytes(raw)
for name,target in [('th14-independent-rng-delivery-worker-nov05.mjs','worker.mjs'),
                    ('th14-independent-rng-delivery-check-nov05.mjs','driver.mjs')]:
    (out/target).write_bytes((R/'tools'/name).read_bytes())
(out/'build-tool.py').write_bytes(Path(__file__).read_bytes())
compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
assert SHA(compiler.read_bytes())=='945cba19ec5c002628bb7d226d21a443198e5da5d9e5430fd2f61b9f143d5309'
argv=[str(compiler),'--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-g0',
      '-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory',
      str(out/'fixture.cpp'),'-o',str(out/'component.wasm')]
(out/'argv.json').write_text(json.dumps(argv,indent=2)+'\n')
with(out/'build.log').open('wb')as log:
    result=subprocess.run(argv,cwd=out,env={**os.environ,'TEMP':str(out),'TMP':str(out)},stdout=log,stderr=subprocess.STDOUT,timeout=90)
assert result.returncode==0,'Compiler diagnostics retained in build.log'
report=dict(compiled=True,headerHashes=headers,fixtureSha256=SHA(raw),
    wasmSha256=SHA((out/'component.wasm').read_bytes()),
    workerSha256=SHA((R/'tools/th14-independent-rng-delivery-worker-nov05.mjs').read_bytes()),
    driverSha256=SHA((R/'tools/th14-independent-rng-delivery-check-nov05.mjs').read_bytes()),
    toolSha256=SHA(Path(__file__).read_bytes()),productionSourcesChanged=False,
    engineObjectsRecompiled=0,originalGameFilesRead=False,completeGame=False)
(out/'build.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(compiled=True,wasmSha256=report['wasmSha256'],engineObjectsRecompiled=0)))
