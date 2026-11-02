"""Recompile the current shake stack producer against original x86/DLL cases."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,subprocess,sys
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
 assert out.is_relative_to(R/'artifacts/th14')and not out.exists();out.mkdir(parents=True)
 spec=importlib.util.spec_from_file_location('storage',R/'tools/th14-test-storage.py');storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage);storage.check_budget(out)
 spec=importlib.util.spec_from_file_location('native',R/'tools/th14-phased-shake-stack-native-nov02.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
 result=native.observe();(out/'native.json').write_text(json.dumps(result,indent=2)+'\n')
 game=R/'runtimes/th12/th12_web/cpp/game';fixture=R/'runtimes/th12/th12_web/tests/cpp/th14-phased-shake-stack-fixture-nov02.cpp'
 compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
 argv=[str(compiler),'--target=wasm32-wasip1','-mexec-model=reactor','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-DPORT_TITLE=14','-I'+str(game),'-Wl,--export-memory','-Wl,--export=stack_case',str(fixture),str(game/'ScreenShake.cpp'),'-o',str(out/'component.wasm')]
 built=subprocess.run(argv,cwd=R,capture_output=True,env={**os.environ,'TEMP':str(out),'TMP':str(out)},timeout=60);(out/'compile.log').write_bytes(built.stdout+built.stderr);assert built.returncode==0,built.stderr.decode(errors='replace')[-2000:]
 files=[Path(__file__),R/'tools/th14-phased-shake-stack-component-check-nov02.mjs',R/'tools/th14-phased-shake-stack-native-nov02.py',fixture,*[game/name for name in ['ScreenShake.hpp','ScreenShake.cpp','NativeStackTh14.hpp','Rng.hpp','Timer.hpp','Types.hpp','PortTitle.hpp']]]
 build=dict(compiled=True,sourceBindings={p.relative_to(R).as_posix():SHA(p.read_bytes())for p in files},argv=argv,wasmSha256=SHA((out/'component.wasm').read_bytes()),compilerSha256=SHA(compiler.read_bytes()))
 (out/'build.json').write_text(json.dumps(build,indent=2)+'\n')
 checked=subprocess.run(['C:/nvm4w/nodejs/node.exe',str(R/'tools/th14-phased-shake-stack-component-check-nov02.mjs'),str(out)],cwd=R,capture_output=True,timeout=60)
 (out/'comparison.log').write_bytes(checked.stdout+checked.stderr);assert checked.returncode==0,checked.stderr.decode(errors='replace')[-2000:]
 storage.check_budget(out);print(checked.stdout.decode(),end='')
if __name__=='__main__':main()
