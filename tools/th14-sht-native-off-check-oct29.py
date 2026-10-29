"""Prove the new SHT import branch compiles out of native worker-off components."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,subprocess
R=Path(__file__).resolve().parents[1];SHA=lambda raw:hashlib.sha256(raw).hexdigest()
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--core-build',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')and not out.exists();out.mkdir(parents=True)
spec=importlib.util.spec_from_file_location('storage',R/'tools/th14-test-storage.py');storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage);storage.check_budget(out,100*1024**3,128*1024**2)
core_raw=a.core_build.resolve(strict=True).read_bytes();core=json.loads(core_raw)
original=next(row for row in core['objectBindings']if Path(row['path']).name=='GameResources.cpp.o');assert SHA(Path(original['path']).read_bytes())==original['sha256']
compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert SHA(compiler.read_bytes())==core['compilerSha256']
flags=['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-g0','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti',
    *['-I'+str(R/'runtimes/th12/th12_web/cpp'/part)for part in ['game','sdl']]]
source=R/'runtimes/th12/th12_web/cpp/game/GameResources.cpp';env=dict(os.environ,TEMP=str(out),TMP=str(out))
result=subprocess.run([str(compiler),*flags,'-c',str(source),'-o',str(out/'GameResources.cpp.o')],env=env,capture_output=True)
(out/'build.log').write_bytes(result.stdout+result.stderr);assert result.returncode==0,result.stderr.decode(errors='replace')
result=subprocess.run([str(compiler),*flags,'-M',str(source)],env=env,capture_output=True);assert result.returncode==0
(out/'dependencies.txt').write_bytes(result.stdout);assert b'ShtTransferTh14.hpp'not in result.stdout
current=(out/'GameResources.cpp.o').read_bytes();assert SHA(current)==original['sha256']and current==Path(original['path']).read_bytes()
report=dict(passed=True,changedSourceObjectByteIdentical=True,workerFeatureOff=True,newTransferHeaderNotIncluded=True,
    sourceSha256=SHA(source.read_bytes()),objectSha256=SHA(current),originalObject=original,
    dependenciesSha256=SHA(result.stdout),coreBuildSha256=SHA(core_raw),compilerSha256=SHA(compiler.read_bytes()),flags=flags,
    toolSha256=SHA(Path(__file__).read_bytes()),newNativeApplicationRunClaimed=False,completeGame=False,nativeEquivalent=False)
(out/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
