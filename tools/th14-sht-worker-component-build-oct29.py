"""Link the actual parsed-SHT consumer to a bounded isolated component host."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,subprocess
R=Path(__file__).resolve().parents[1];SHA=lambda raw:hashlib.sha256(raw).hexdigest()
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--core-build',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')and not out.exists();out.mkdir(parents=True)
spec=importlib.util.spec_from_file_location('storage',R/'tools/th14-test-storage.py');storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage)
budget=lambda:storage.check_budget(out,100*1024**3,128*1024**2);budget()
core_raw=a.core_build.resolve(strict=True).read_bytes();core=json.loads(core_raw);assert len(core['objectBindings'])==141 and core['compiled']
objects=[]
for row in core['objectBindings']:
    path=Path(row['path']);assert SHA(path.read_bytes())==row['sha256']
    if path.name!='GameResources.cpp.o':objects.append(row)
assert len(objects)==140
compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert SHA(compiler.read_bytes())==core['compilerSha256']
flags=['--target=wasm32-wasip1','-DPORT_TITLE=14','-DTH14_WEBGPU_BACKEND=1','-DTH14_ARCHIVE_WORKER=1','-std=c++17','-O2','-g0','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti',
    *['-I'+str(R/'runtimes/th12/th12_web/cpp'/part)for part in ['game','sdl']]]
env=dict(os.environ,TEMP=str(out),TMP=str(out));bindings={}
for relative in ['runtimes/th12/th12_web/cpp/game/GameResources.cpp','runtimes/th12/th12_web/tests/cpp/th14-sht-worker-fixture.cpp']:
    path=R/relative;bindings[relative]=SHA(path.read_bytes());obj=out/(path.name+'.o')
    result=subprocess.run([str(compiler),*flags,'-c',str(path),'-o',str(obj)],env=env,capture_output=True)
    (out/(path.stem+'.log')).write_bytes(result.stdout+result.stderr);assert result.returncode==0,result.stderr.decode(errors='replace')[-4000:]
    objects.append(dict(path=obj.as_posix(),sha256=SHA(obj.read_bytes())))
link=['-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576']
result=subprocess.run([str(compiler),*flags,*link,*[row['path']for row in objects],'-o',str(out/'consumer.wasm')],env=env,capture_output=True)
(out/'link.log').write_bytes(result.stdout+result.stderr);assert result.returncode==0,result.stderr.decode(errors='replace')[-4000:]
for name,digest in core['headerHashes'].items():
    path=R/'runtimes/th12'/name;assert SHA(path.read_bytes())==digest,name;bindings[path.relative_to(R).as_posix()]=digest
path=R/'runtimes/th12/th12_web/cpp/game/ShtTransferTh14.hpp';bindings[path.relative_to(R).as_posix()]=SHA(path.read_bytes())
report=dict(compiled=True,wasmSha256=SHA((out/'consumer.wasm').read_bytes()),objectBindings=objects,sourceBindings=bindings,
    reusedProductionCoreObjects=140,compiledProductionCoreObjects=1,productionConsumer=True,workerFeatureEnabled=True,
    coreBuildSha256=SHA(core_raw),compilerSha256=SHA(compiler.read_bytes()),toolSha256=SHA(Path(__file__).read_bytes()),flags=flags,linkFlags=link,
    noGpuAudioOrGameState=True,browserAcceptance=False,completeGame=False,nativeEquivalent=False)
(out/'build.json').write_text(json.dumps(report,indent=2)+'\n');budget();print(json.dumps({key:report[key]for key in ['compiled','wasmSha256','reusedProductionCoreObjects','compiledProductionCoreObjects','productionConsumer']}))
