"""Link a clock-observation fixture to verified production TH14 engine objects."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,subprocess
R=Path(__file__).resolve().parents[1];SHA=lambda raw:hashlib.sha256(raw).hexdigest()
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--core-build',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();out=args.output.resolve();assert out.is_relative_to(R/'artifacts/th14')and not out.exists();out.mkdir(parents=True)
spec=importlib.util.spec_from_file_location('storage',R/'tools/th14-test-storage.py');storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage)
storage.check_budget(out,100*1024**3,128*1024**2)
core_raw=args.core_build.resolve(strict=True).read_bytes();core=json.loads(core_raw)
assert core['compiled']and core['readOnlyObserver']and len(core['objectBindings'])==141
for row in core['objectBindings']:assert SHA(Path(row['path']).read_bytes())==row['sha256']
dependencies={}
for name,digest in core['headerHashes'].items():
    path=R/'runtimes/th12'/name;assert SHA(path.read_bytes())==digest,name;dependencies[path.as_posix()]=digest
fixture=R/'runtimes/th12/th12_web/tests/cpp/th14-normal-worker-fixture.cpp'
for path in [fixture,fixture.parent/'th14-native-campaign-fixture.cpp']:dependencies[path.as_posix()]=SHA(path.read_bytes())
compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert SHA(compiler.read_bytes())==core['compilerSha256']
flags=['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-g0','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti',
    *['-I'+str(R/'runtimes/th12/th12_web/cpp'/part)for part in ['game','sdl']]]
link=['-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576']
result=subprocess.run([str(compiler),*flags,*link,str(fixture),*[row['path']for row in core['objectBindings']],'-o',str(out/'observer.wasm')],
    env=dict(os.environ,TEMP=str(out),TMP=str(out)),capture_output=True)
(out/'build.log').write_bytes(result.stdout+result.stderr);assert result.returncode==0,result.stderr.decode(errors='replace')[-4000:]
for path,digest in dependencies.items():assert SHA(Path(path).read_bytes())==digest
report={**core,'fixtureGraphRoot':fixture.as_posix(),'expandedFixtureSha256':SHA(fixture.read_bytes()),'fixtureDependencyHashes':dependencies,
    'fixtureConservativeHeaderInventory':True,'wasmSha256':SHA((out/'observer.wasm').read_bytes()),'flags':flags,'linkFlags':link,
    'engineSourcesRecompiledForThisLink':0,'engineObjectsReusedForThisLink':141,'testOnlyExternalHostClockObservation':True,
    'vmCallbackPointersWrapped':False,'nativeRngCounterInputOrPointerValuesProvided':False,
    'productionNormalAnmBoundaryPoll':True,'reuseBuildSha256':SHA(core_raw),'buildToolSha256':SHA(Path(__file__).read_bytes()),'completeGame':False,'nativeEquivalent':False}
(out/'observer-build.json').write_text(json.dumps(report,indent=2)+'\n');storage.check_budget(out,100*1024**3,128*1024**2)
print(json.dumps(dict(compiled=True,objectsReused=141,wasmSha256=report['wasmSha256'],vmCallbackPointersWrapped=False)))
