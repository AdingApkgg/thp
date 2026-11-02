"""Recompile current Rng and compare its scoped boundaries to original x86."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,subprocess,sys
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()

def module(path):
    spec=importlib.util.spec_from_file_location(path.stem,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def run(home):
    home=home.resolve();assert home.is_relative_to(R/'artifacts/th14')and not home.exists();home.mkdir(parents=True)
    storage=module(R/'tools/th14-test-storage.py');storage.check_budget(home,100*1024**3,128*1024**2)
    native_tool=R/'tools/th14-rng-store-boundary-native-nov02.py';native=module(native_tool).observe()
    (home/'native.json').write_text(json.dumps(native,indent=2)+'\n',encoding='utf8')
    fixture=R/'runtimes/th12/th12_web/tests/cpp/th14-rng-store-boundary-fixture-nov02.cpp'
    game=R/'runtimes/th12/th12_web/cpp/game';compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
    exports=['rng_case','rng_atomic_case','scope_lifetime_case','scope_failure_case','scope_reentry_case']
    argv=[str(compiler),'--target=wasm32-wasip1','-mexec-model=reactor','-std=c++20','-O2','-fno-exceptions','-DPORT_TITLE=14','-I'+str(game),str(fixture),'-Wl,--export-memory',*['-Wl,--export='+x for x in exports],'-o',str(home/'fixture.wasm')]
    compiled=subprocess.run(argv,cwd=R,capture_output=True,timeout=120,env={**os.environ,'TMP':str(home),'TEMP':str(home)})
    (home/'compile.log').write_bytes(compiled.stdout+compiled.stderr);assert compiled.returncode==0
    bindings={}
    for p in [Path(__file__),native_tool,fixture,game/'Rng.hpp',game/'Types.hpp',game/'PortTitle.hpp',home/'fixture.wasm']:
        raw=p.read_bytes();bindings[p.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw))
    (home/'build.json').write_text(json.dumps(dict(argv=argv,bindings=bindings,compilerSha256=SHA(compiler.read_bytes()),wasmSha256=SHA((home/'fixture.wasm').read_bytes()),productionChanged=False),indent=2)+'\n',encoding='utf8')
    runner=R/'tools/th14-rng-store-boundary-component-check-nov02.mjs'
    # The local Node executable is an existing workspace dependency.
    checked=subprocess.run(['C:/nvm4w/nodejs/node.exe',str(runner),str(home)],cwd=R,capture_output=True,timeout=60)
    (home/'comparison.log').write_bytes(checked.stdout+checked.stderr);assert checked.returncode==0,checked.stderr.decode(errors='replace')[-1600:]
    result=json.loads((home/'component-verified.json').read_bytes());assert result['cases']==800 and result['scopedObserverLifetimeFailureAndReentryControlsPassed']
    storage.check_budget(home,100*1024**3,128*1024**2)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=run(a.output);print(json.dumps(result),flush=True)
