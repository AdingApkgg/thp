"""Build published-vs-current ECL include assembly/lookup component controls."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,subprocess,sys
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base-commit',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();c=R/'tools/tmp/github-source-release'
    assert out.is_relative_to(R/'artifacts/th14')and not out.exists();out.mkdir(parents=True)
    spec=importlib.util.spec_from_file_location('ecl_program_storage',R/'tools/th14-test-storage.py');storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage)
    budget=lambda:storage.check_budget(out,100*1024**3,128*1024**2);budget()
    sdk=R/'runtimes/th12/tools/emsdk';emcc=sdk/'upstream/emscripten/emcc.py';env={**os.environ,'EM_CONFIG':str(sdk/'.emscripten'),'EMSDK':str(sdk),'EMSDK_PYTHON':sys.executable,'EMCC_CORES':'2','TEMP':str(out),'TMP':str(out),'TMPDIR':str(out)}
    report=dict(publishedBase=a.base_commit,toolSha256=SHA(Path(__file__).read_bytes()),builds={},completeGame=False,nativeEquivalent=False)
    names=['Archive.cpp','Archive.hpp','ResourceCrypt.cpp','ResourceCrypt.hpp','Lzss.cpp','Lzss.hpp','Types.hpp','PortTitle.hpp','EclResource.cpp','EclResource.hpp','AnmResource.hpp','AnmTransferTh14.hpp']
    for variant in ('published','current'):
        home=out/variant;game=home/'source/th12_web/cpp/game';game.mkdir(parents=True);bindings={}
        for name in names:
            path='runtimes/th12/th12_web/cpp/game/'+name
            raw=(R/path).read_bytes()if variant=='current'and name in ('EclResource.cpp','EclResource.hpp')else subprocess.check_output(['git','-C',str(c),'show',a.base_commit+':'+path])
            (game/name).write_bytes(raw);bindings[path]=SHA(raw)
        assert bindings['runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp']=='d57118f1114f3909c42a2e99e7df30e625f6563247a8118cd14bb9f68a0f97ef'
        fixture=R/'runtimes/th12/th12_web/tests/cpp/th14-ecl-program-transfer-regression.cpp';target=home/'source/th12_web/tests/cpp'/fixture.name;target.parent.mkdir(parents=True);target.write_bytes(fixture.read_bytes());bindings[fixture.relative_to(R).as_posix()]=SHA(fixture.read_bytes())
        exports=['malloc','free',*['fixture_'+n for n in ('open','name','program','size','error')]]
        cmd=[sys.executable,str(emcc),'-O2','-std=c++17','-ffp-contract=off','-fno-exceptions','-fno-rtti','-DPORT_TITLE=14',*[str(game/n)for n in ('Archive.cpp','ResourceCrypt.cpp','Lzss.cpp','EclResource.cpp')],str(target),'--no-entry','-sDEFAULT_TO_CXX=1','-sFILESYSTEM=0','-sMODULARIZE=1','-sEXPORT_ES6=1','-sENVIRONMENT=web,worker,node','-sALLOW_MEMORY_GROWTH=1','-sINITIAL_MEMORY=134217728','-sMAXIMUM_MEMORY=536870912','-sEXPORTED_FUNCTIONS='+','.join('_'+n for n in exports),'-sEXPORTED_RUNTIME_METHODS=HEAPU8,UTF8ToString','-o',str(home/'fixture.mjs')]
        (home/'command.json').write_text(json.dumps(cmd,indent=2)+'\n');result=subprocess.run(cmd,env=env,capture_output=True);(home/'build.log').write_bytes(result.stdout+result.stderr);assert result.returncode==0,(home/'build.log').read_text()[-5000:]
        budget();report['builds'][variant]=dict(sourceBindings=bindings,wasmSha256=SHA((home/'fixture.wasm').read_bytes()),loaderSha256=SHA((home/'fixture.mjs').read_bytes()))
    (out/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(compiled=True,variants=list(report['builds']),completeGame=False)))
if __name__=='__main__':main()
