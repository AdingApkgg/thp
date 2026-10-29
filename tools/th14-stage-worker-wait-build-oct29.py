"""Compile the actual TH14 worker minimum-wait helper for finite host tests."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,subprocess
R=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();out=args.output.resolve();assert out.is_relative_to(R/'artifacts/th14')and not out.exists();out.mkdir(parents=True)
spec=importlib.util.spec_from_file_location('storage',R/'tools/th14-test-storage.py');storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage)
storage.check_budget(out,100*1024**3,128*1024**2)
sha=lambda raw:hashlib.sha256(raw).hexdigest()
compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
sources=['runtimes/th12/th12_web/tests/cpp/th14-stage-worker-wait-fixture.cpp','runtimes/th12/th12_web/cpp/sdl/StageWorkerWaitTh14.hpp','runtimes/th12/th12_web/cpp/game/Types.hpp']
bindings={name:sha((R/name).read_bytes())for name in sources}
flags=['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-g0','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory']
result=subprocess.run([str(compiler),*flags,str(R/sources[0]),'-o',str(out/'wait.wasm')],env=dict(os.environ,TEMP=str(out),TMP=str(out)),capture_output=True)
(out/'build.log').write_bytes(result.stdout+result.stderr);assert result.returncode==0,result.stderr.decode(errors='replace')
assert bindings=={name:sha((R/name).read_bytes())for name in sources}
report=dict(compiled=True,sourceBindings=bindings,flags=flags,wasmSha256=sha((out/'wait.wasm').read_bytes()),compilerSha256=sha(compiler.read_bytes()),toolSha256=sha(Path(__file__).read_bytes()),completeGame=False,nativeEquivalent=False)
(out/'build.json').write_text(json.dumps(report,indent=2)+'\n');storage.check_budget(out,100*1024**3,128*1024**2)
print(json.dumps(report))
