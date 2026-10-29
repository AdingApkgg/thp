"""Link actual browser C++ resource objects to a finite comparison fixture."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,subprocess,sys
R=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--suite',choices=['stage','selected-player','core-tail','bootstrap','later-stage'],default='stage')
    a=p.parse_args();B=a.build.resolve(strict=True);O=a.output.resolve()
    assert B.is_relative_to(R/'artifacts/th14') and O.is_relative_to(R/'artifacts/th14') and not O.exists()
    O.mkdir(parents=True)
    storage_path=R/'tools/th14-test-storage.py'
    spec=importlib.util.spec_from_file_location('background_storage',storage_path)
    storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage)
    budget=lambda:storage.check_budget(O,100*1024**3,128*1024**2)
    budget();raw=(B/'build.json').read_bytes();build=json.loads(raw);assert build['compiled'] and build['backgroundArchiveIntegration']
    bindings={};source=O/'source'
    for relative,row in build['sourceBindings'].items():
        if Path(relative).suffix not in ('.hpp','.h','.inc'):continue
        original=B/'source'/relative;data=original.read_bytes();assert SHA(data)==row['sha256']
        target=source/relative;target.parent.mkdir(parents=True,exist_ok=True);os.link(original,target)
        bindings[relative]=row['sha256']
    fixture_name={'stage':'th14-background-resource-fixture.cpp','selected-player':'th14-selected-player-worker-fixture.cpp','core-tail':'th14-core-tail-worker-fixture.cpp','bootstrap':'th14-bootstrap-worker-fixture.cpp','later-stage':'th14-later-stage-worker-fixture.cpp'}[a.suite]
    for name in (fixture_name,'th14-initial-stage-decode-fixture.cpp'):
        original=R/'runtimes/th12/th12_web/tests/cpp'/name;data=original.read_bytes()
        target=source/'th12_web/tests/cpp'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        bindings['th12_web/tests/cpp/'+name]=SHA(data)
    library=B/'source/portable/sdl/Th14WebGpuLibrary.js'
    assert SHA(library.read_bytes())==build['sourceBindings']['portable/sdl/Th14WebGpuLibrary.js']['sha256']
    objects=[];object_bindings={}
    for relative,digest in build['objectHashes'].items():
        if not relative.startswith('th12_web/cpp/game/'):continue
        path=B/'objects'/(relative.replace('/','_')+'.o');assert SHA(path.read_bytes())==digest
        objects.append(path);object_bindings[relative]=digest
    assert len(objects)==141
    sdk=R/'runtimes/th12/tools/emsdk';emcc=sdk/'upstream/emscripten/emcc.py'
    env={**os.environ,'EM_CONFIG':str(sdk/'.emscripten'),'EMSDK':str(sdk),'EMSDK_PYTHON':sys.executable,'EMCC_CORES':'2',
        'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)}
    methods={'stage':('open','prepare','names','step','compare','read','anm','std','ecl','error'),
        'selected-player':('open','select','name','load','cancel','empty','compare','sync','error'),
        'core-tail':('open','reset','load','empty','compare','error'),
        'bootstrap':('open','reset','signature','load','empty','compare','error'),
        'later-stage':('open','prepare','advance','names','dispatch','deliver','publish','finish','cancel','suspend','resume','gpu','counts','wrong_owner','compare','error')}[a.suite]
    exports=['malloc','free',*['fixture_'+name for name in methods]]
    command=[sys.executable,str(emcc),*build['flags'],str(source/'th12_web/tests/cpp'/fixture_name),
        *map(str,objects),'--no-entry','-sDEFAULT_TO_CXX=1','-sMODULARIZE=1','-sEXPORT_ES6=1','-sENVIRONMENT=web,worker,node',
        '-sFILESYSTEM=0','-sALLOW_MEMORY_GROWTH=1','-sINITIAL_MEMORY=536870912','-sMAXIMUM_MEMORY=1073741824',
        '-sSTACK_SIZE=1048576','-sEXPORTED_FUNCTIONS='+','.join('_'+name for name in exports),
        '-sEXPORTED_RUNTIME_METHODS=HEAPU8,UTF8ToString','--js-library',str(library),'-o',str(O/'resources.mjs')]
    (O/'command.json').write_text(json.dumps(command,indent=2)+'\n')
    result=subprocess.run(command,env=env,capture_output=True);(O/'build.log').write_bytes(result.stdout+result.stderr)
    assert result.returncode==0,(O/'build.log').read_text()[-6000:]
    budget()
    report=dict(compiled=True,browserBuildSha256=SHA(raw),objectBindings=object_bindings,sourceBindings=bindings,
        mainGameResourceObjectUsed=True,wasmSha256=SHA((O/'resources.wasm').read_bytes()),
        loaderSha256=SHA((O/'resources.mjs').read_bytes()),toolSha256=SHA(Path(__file__).read_bytes()),
        noGraphicsOrAudioDevice=True,completeGame=False,nativeEquivalent=False)
    (O/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k not in ('objectBindings','sourceBindings')}))
if __name__=='__main__':main()
