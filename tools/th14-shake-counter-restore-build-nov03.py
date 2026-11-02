from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/frame-rng-scope-nov02/counter-integrated-component';H.mkdir(exist_ok=False);sha=lambda b:hashlib.sha256(b).hexdigest()
game=R/'runtimes/th12/th12_web/cpp/game';fixture=R/'runtimes/th12/th12_web/tests/cpp/th14-shake-counter-restore-fixture-nov03.cpp';compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
source=[game/n for n in ['ScreenShake.cpp','ScreenShake.hpp','NativeStackTh14.hpp','Rng.hpp','Timer.hpp','Types.hpp','PortTitle.hpp']]+[fixture]
argv=[str(compiler),'--target=wasm32-wasip1','-mexec-model=reactor','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-DPORT_TITLE=14','-I'+str(game),'-Wl,--export-memory','-Wl,--export=stack_case',str(fixture),str(game/'ScreenShake.cpp'),'-o',str(H/'component.wasm')]
p=subprocess.run(argv,cwd=R,capture_output=True,env={**os.environ,'TEMP':str(H),'TMP':str(H)},timeout=60);(H/'compile.log').write_bytes(p.stdout+p.stderr);assert p.returncode==0,p.stderr.decode(errors='replace')[-2000:]
(H/'build.json').write_text(json.dumps({'sourceHashes':{p.relative_to(R).as_posix():sha(p.read_bytes()) for p in source},'wasmSha256':sha((H/'component.wasm').read_bytes()),'argv':argv},indent=2)+'\n')
subprocess.run(['C:/nvm4w/nodejs/node.exe','--no-warnings',str(R/'tools/th14-shake-counter-restore-check-nov03.mjs')],cwd=R,check=True)
