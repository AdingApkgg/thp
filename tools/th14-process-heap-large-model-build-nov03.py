"""Build an isolated higher-capacity copy of the existing finite heap candidate."""
from pathlib import Path
import hashlib,json,subprocess
R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/replay-candidates-second-nov03/process-heap-model-large';H.mkdir(exist_ok=True);assert not any(H.iterdir())
source=R/'tools/th14-process-heap-model-nov03.cpp';raw=source.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(raw)=='a07b7aa9f4a9ceae83209b439ae01bee587dbc0331edd73c6db78a15f195a7b1'
text=raw.decode('utf8');assert text.count('128')==9;text=text.replace('128','2048');large=H/'large.cpp';large.write_text(text,encoding='utf8')
compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';obj=H/'large.o';wasm=H/'large.wasm'
for cmd in [[str(compiler),'--target=wasm32-wasip1','-std=c++17','-O2','-c',str(large),'-o',str(obj)],[str(compiler),'--target=wasm32-wasip1','-mexec-model=reactor',*[f'-Wl,--export={name}' for name in ['heap_model_reset','heap_model_alloc','heap_model_free','heap_model_ok']],str(obj),'-o',str(wasm)]]:
 subprocess.run(cmd,cwd=R,check=True,capture_output=True,timeout=120)
result=dict(baseSourceSha256=sha(raw),derivedSourceSha256=sha(large.read_bytes()),compilerSha256=sha(compiler.read_bytes()),wasmSha256=sha(wasm.read_bytes()),onlyChange='replace nine 128-slot limits with 2048',productionIntegrated=False,completeGame=False,nativeEquivalent=False,toolSha256=sha(Path(__file__).read_bytes()))
(H/'build.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
