"""Compile all TH14 core objects after the initialization callback changes class layout."""
from pathlib import Path
import concurrent.futures,hashlib,json,os,re,subprocess,time
R=Path(__file__).resolve().parents[1]
import argparse
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--base-build',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
O=args.output.resolve();assert O.is_relative_to(R/'artifacts/th14')and not O.exists();O.mkdir()
B=args.base_build.resolve();assert B.is_relative_to(R/'artifacts/th14')
base=json.loads(B.read_bytes());SHA=lambda b:hashlib.sha256(b).hexdigest()
assert SHA(B.read_bytes())=='341a741b5e6438eb360234c4b7e4be5ad91cd646eb9af8418513f27e47b769cf'
import importlib.util
spec=importlib.util.spec_from_file_location('storage',R/'tools/th14-test-storage.py');storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage);storage.check_budget(O,100*1024**3,128*1024**2)
source=O/'source';inputs={}
for name in {**base['sourceHashes'],**base['headerHashes']}:
    p=R/'runtimes/th12'/name
    if name=='th12_web/cpp/game/ResourceCrypt.cpp'and SHA(p.read_bytes())!='d57118f1114f3909c42a2e99e7df30e625f6563247a8118cd14bb9f68a0f97ef':p=R/'tools/tmp/github-source-release/runtimes/th12'/name
    assert not name.startswith('/')and '..'not in Path(name).parts
    if name=='th12_web/cpp/game/ResourceCrypt.cpp':assert SHA(p.read_bytes())=='d57118f1114f3909c42a2e99e7df30e625f6563247a8118cd14bb9f68a0f97ef'
    raw=p.read_bytes();inputs[name]=dict(bytes=len(raw),sha256=SHA(raw))
    q=source/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(raw)
fixture=R/'runtimes/th12/th12_web/tests/cpp/th14-initialization-clock-fixture-nov01.cpp'
fixture_dependencies={}
def scan_fixture(path):
    path=path.resolve();key=path.as_posix()
    if key in fixture_dependencies:return
    raw=path.read_bytes();fixture_dependencies[key]=SHA(raw)
    for name in re.findall(r'^\s*#\s*include\s*"([^"]+)"',raw.decode(),re.M):
        candidates=[path.parent/name,*[source/'th12_web/cpp'/part/name for part in ['game','sdl']]]
        child=next((p for p in candidates if p.exists()),None);assert child,name;scan_fixture(child)
scan_fixture(fixture)
compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert SHA(compiler.read_bytes())==base['compilerSha256']
flags=[x for x in base['flags']if not x.startswith('-I')]+['-I'+str(source/'th12_web/cpp'/part)for part in ['game','sdl']]
env=dict(os.environ,TEMP=str(O),TMP=str(O));objects=O/'objects';objects.mkdir();started=time.monotonic()
def compile_unit(name):
 p=source/name;o=objects/(p.name+'.o');run=subprocess.run([str(compiler),*flags,'-c',str(p),'-o',str(o)],capture_output=True,env=env)
 (objects/(p.name+'.log')).write_bytes(run.stdout+run.stderr);assert not run.returncode,(name,run.stderr.decode(errors='replace')[-1500:])
 return dict(path=o.as_posix(),sha256=SHA(o.read_bytes()))
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:rows=list(pool.map(compile_unit,base['sourceHashes']))
result=subprocess.run([str(compiler),*flags,*base['linkFlags'],str(fixture),*[x['path']for x in rows],'-o',str(O/'observer.wasm')],capture_output=True,env=env)
(O/'link.log').write_bytes(result.stdout+result.stderr);assert not result.returncode,result.stderr.decode(errors='replace')[-2000:]
sources={name:SHA((source/name).read_bytes())for name in base['sourceHashes']};headers={name:SHA((source/name).read_bytes())for name in base['headerHashes']}
for name,digest in fixture_dependencies.items():assert SHA(Path(name).read_bytes())==digest
report={**base,'sourceHashes':sources,'headerHashes':headers,'objectBindings':rows,'flags':flags,'wasmSha256':SHA((O/'observer.wasm').read_bytes()),'sourceSnapshotRoot':source.as_posix(),'baseInputs':inputs,'fixtureGraphRoot':fixture.as_posix(),'expandedFixtureSha256':SHA(fixture.read_bytes()),'fixtureDependencyHashes':fixture_dependencies,'fixtureConservativeHeaderInventory':True,'isolatedPrototypeOnly':False,'rootProductionSourcesModified':True,'initializationReentryGuard':True,'all141ObjectsRecompiledForChangedClassLayout':True,'unrelatedWorkingTreeSourceEditsExcluded':['th12_web/cpp/game/ResourceCrypt.cpp']if inputs['th12_web/cpp/game/ResourceCrypt.cpp']['sha256']!=SHA((R/'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp').read_bytes())else[],'buildToolSha256':SHA(Path(__file__).read_bytes()),'elapsedSeconds':time.monotonic()-started,'completeGame':False,'nativeEquivalent':False}
storage.check_budget(O,100*1024**3,128*1024**2)
(O/'observer-build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(compiled=True,objects=len(rows),elapsedSeconds=report['elapsedSeconds'],wasmSha256=report['wasmSha256'])),flush=True)
