"""Build the isolated TH14 CPU archive-worker prototype, without game integration."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,subprocess,sys

R=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base-commit',required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();O=args.output.resolve();C=R/'tools/tmp/github-source-release'
    assert O.is_relative_to(R/'artifacts/th14')and not O.exists()
    subprocess.run(['git','-C',str(C),'cat-file','-e',args.base_commit+'^{commit}'],check=True)
    O.mkdir(parents=True);source=O/'source';source.mkdir();bindings={}
    storage_path=R/'tools/th14-test-storage.py'
    spec=importlib.util.spec_from_file_location('archive_worker_storage',storage_path)
    storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage)
    tool=Path(__file__).read_bytes();(O/'build-tool.py').write_bytes(tool)
    (O/'storage-tool.py').write_bytes(storage_path.read_bytes())
    storage.check_budget(O,maximum_case=128*1024**2)
    for name in ('Archive.cpp','Archive.hpp','ResourceCrypt.cpp','ResourceCrypt.hpp','Lzss.cpp','Lzss.hpp','Types.hpp'):
        path='runtimes/th12/th12_web/cpp/game/'+name
        raw=subprocess.check_output(['git','-C',str(C),'show',args.base_commit+':'+path])
        (source/name).write_bytes(raw);bindings[path]=dict(bytes=len(raw),sha256=SHA(raw))
    assert bindings['runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp']['sha256']=='d57118f1114f3909c42a2e99e7df30e625f6563247a8118cd14bb9f68a0f97ef'
    for name in ('archive-decoder.cpp','archive-decode-client.mjs','archive-decode-endpoint.mjs','archive-decode-worker.mjs'):
        path=R/'tools/th14-archive-worker'/name;raw=path.read_bytes()
        (O/name).write_bytes(raw);bindings[path.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw))
    sdk=R/'runtimes/th12/tools/emsdk';emcc=sdk/'upstream/emscripten/emcc.py'
    env={**os.environ,'EM_CONFIG':str(sdk/'.emscripten'),'EMSDK':str(sdk),'EMSDK_PYTHON':sys.executable,'EMCC_CORES':'2',
         'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)}
    exports='malloc,free,decoder_open,decoder_name,decoder_read,decoder_size,decoder_error,decoder_close'
    command=[sys.executable,str(emcc),'-O2','-std=c++17','-fno-exceptions','-fno-rtti','-DPORT_TITLE=14','-I'+str(source),
        *[str(source/name)for name in ('Archive.cpp','ResourceCrypt.cpp','Lzss.cpp')],str(O/'archive-decoder.cpp'),'--no-entry',
        '-sDEFAULT_TO_CXX=1','-sFILESYSTEM=0','-sMODULARIZE=1','-sEXPORT_ES6=1','-sENVIRONMENT=web,worker,node',
        '-sALLOW_MEMORY_GROWTH=1','-sINITIAL_MEMORY=134217728','-sMAXIMUM_MEMORY=536870912','-sSTACK_SIZE=1048576',
        '-sEXPORTED_FUNCTIONS='+','.join('_'+name for name in exports.split(',')),
        '-sEXPORTED_RUNTIME_METHODS=HEAPU8,UTF8ToString','-o',str(O/'archive-decoder.mjs')]
    (O/'command.json').write_text(json.dumps(command,indent=2)+'\n')
    result=subprocess.run(command,env=env,capture_output=True)
    (O/'build.log').write_bytes(result.stdout+result.stderr)
    assert result.returncode==0,(O/'build.log').read_text()[-4000:]
    storage.check_budget(O,maximum_case=128*1024**2)
    wasm=(O/'archive-decoder.wasm').read_bytes()
    report=dict(compiled=True,publishedBase=args.base_commit,sourceBindings=bindings,
        wasmBytes=len(wasm),wasmSha256=SHA(wasm),loaderSha256=SHA((O/'archive-decoder.mjs').read_bytes()),
        buildToolSha256=SHA(tool),storageToolSha256=SHA((O/'storage-tool.py').read_bytes()),
        compilerVersion=(sdk/'upstream/emscripten/emscripten-version.txt').read_text().strip(),
        productionIntegrated=False,browserAcceptance=False,completeGame=False,nativeEquivalent=False)
    (O/'build.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items()if k!='sourceBindings'}))

if __name__=='__main__':main()
