"""Build the finite production ANM parser/worker-transfer comparison boundary."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,subprocess,sys
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--worker-build',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();worker=a.worker_build.resolve(strict=True);out=a.output.resolve()
    assert worker.is_relative_to(R/'artifacts/th14')and out.is_relative_to(R/'artifacts/th14')and not out.exists()
    out.mkdir(parents=True);source=out/'source';game=source/'th12_web/cpp/game';game.mkdir(parents=True)
    storage_path=R/'tools/th14-test-storage.py';spec=importlib.util.spec_from_file_location('anm_storage',storage_path);storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage)
    budget=lambda:storage.check_budget(out,100*1024**3,128*1024**2);budget()
    build_raw=(worker/'build.json').read_bytes();build=json.loads(build_raw);assert build['compiled']and build['actualProductionAnmParser']and build['browserRuntimeModules']
    bindings={}
    for path,row in build['sourceBindings'].items():
        if not path.startswith('runtimes/th12/th12_web/cpp/game/'):continue
        original=worker/'source'/Path(path).name;raw=original.read_bytes();assert SHA(raw)==row['sha256'];(game/Path(path).name).write_bytes(raw);bindings[path]=row
    fixture=R/'runtimes/th12/th12_web/tests/cpp/th14-anm-transfer-fixture.cpp';target=source/'th12_web/tests/cpp'/fixture.name;target.parent.mkdir(parents=True);target.write_bytes(fixture.read_bytes());bindings[fixture.relative_to(R).as_posix()]=dict(bytes=fixture.stat().st_size,sha256=SHA(fixture.read_bytes()))
    sdk=R/'runtimes/th12/tools/emsdk';emcc=sdk/'upstream/emscripten/emcc.py';env={**os.environ,'EM_CONFIG':str(sdk/'.emscripten'),'EMSDK':str(sdk),'EMSDK_PYTHON':sys.executable,'EMCC_CORES':'2','TEMP':str(out),'TMP':str(out),'TMPDIR':str(out)}
    cmd=[sys.executable,str(emcc),'-O2','-std=c++17','-ffp-contract=off','-fno-exceptions','-fno-rtti','-DPORT_TITLE=14',str(game/'AnmResource.cpp'),str(target),'--no-entry','-sDEFAULT_TO_CXX=1','-sFILESYSTEM=0','-sMODULARIZE=1','-sEXPORT_ES6=1','-sENVIRONMENT=web,worker,node','-sALLOW_MEMORY_GROWTH=1','-sINITIAL_MEMORY=134217728','-sMAXIMUM_MEMORY=536870912','-sEXPORTED_FUNCTIONS=_malloc,_free,_fixture_compare,_fixture_count,_fixture_reject','-sEXPORTED_RUNTIME_METHODS=HEAPU8','-o',str(out/'fixture.mjs')]
    (out/'command.json').write_text(json.dumps(cmd,indent=2)+'\n');result=subprocess.run(cmd,env=env,capture_output=True);(out/'build.log').write_bytes(result.stdout+result.stderr);assert result.returncode==0,(out/'build.log').read_text()[-5000:]
    budget();report=dict(compiled=True,workerBuildPath=str(worker.relative_to(R)),workerBuildSha256=SHA(build_raw),sourceBindings=bindings,wasmSha256=SHA((out/'fixture.wasm').read_bytes()),loaderSha256=SHA((out/'fixture.mjs').read_bytes()),toolSha256=SHA(Path(__file__).read_bytes()),completeGame=False,nativeEquivalent=False)
    (out/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='sourceBindings'}))
if __name__=='__main__':main()
