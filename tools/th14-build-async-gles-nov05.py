"""Rebuild TH14 GLES Application with Asyncify-owned callback stacks.

The 145 unchanged objects and their complete frozen sources are hash checked.
The added header is included only by Application, which is recompiled. No
assets or original observation values are inputs to this build.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys

R=Path(__file__).resolve().parents[1]
BASE=R/'artifacts/th14/gles-clip-portable-nov04/browser-gles-nov05'
SHA=lambda b:hashlib.sha256(b).hexdigest()

def main(out):
    assert not out.exists();out.mkdir(parents=True);objects=out/'objects';objects.mkdir()
    base_raw=(BASE/'build.json').read_bytes();base=json.loads(base_raw)
    assert base['wasmSha256']=='0a9750bfe24129ec6005b197fe599b49c2adb62652e175c85e8c0b479f616794'
    source=out/'source';app_name='th12_web/cpp/sdl/Application.cpp'
    overlays=[app_name,'portable/sdl/Th14AsyncCallbacks.hpp','portable/sdl/Th14AsyncRuntime.mjs']
    inventory=dict(base['sourceBindings'])
    for name,row in base['sourceBindings'].items():assert SHA((BASE/'source'/name).read_bytes())==row['sha256'],name
    for path in (BASE/'source').rglob('*'):
        if not path.is_file():continue
        name=path.relative_to(BASE/'source').as_posix()
        if name in overlays:continue
        dest=source/name;dest.parent.mkdir(parents=True,exist_ok=True);os.link(path,dest)
    for name in overlays:
        raw=(R/'runtimes/th12'/name).read_bytes();dest=source/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
        inventory[name]=dict(bytes=len(raw),sha256=SHA(raw),origin='asyncify-gles-callback-fix')
    # The new header must affect Application alone; every other input stays frozen.
    for path in source.rglob('*'):
        if path.suffix not in ['.cpp','.hpp','.h','.inc'] or path.relative_to(source).as_posix() in overlays:continue
        assert b'Th14AsyncCallbacks.hpp' not in path.read_bytes(),str(path)
    sdk=R/'runtimes/th12/tools/emsdk';emcc=sdk/'upstream/emscripten/emcc.py'
    env={**os.environ,'EM_CONFIG':str(sdk/'.emscripten'),'EMSDK':str(sdk),'EMSDK_PYTHON':sys.executable,'EMCC_CORES':'2',
        'TEMP':str(objects),'TMP':str(objects),'TMPDIR':str(objects)}
    obj=objects/(app_name.replace('/','_')+'.o');inputs=[];reused={}
    for name,digest in base['objectHashes'].items():
        if name==app_name:inputs.append(obj);continue
        old=BASE/'objects'/(name.replace('/','_')+'.o');assert SHA(old.read_bytes())==digest
        inputs.append(old);reused[name]=digest
    assert len(inputs)==146 and len(reused)==145
    link_flags=list(base['linkFlags'])
    index=next(i for i,x in enumerate(link_flags)if x.startswith('-sEXPORTED_FUNCTIONS='))
    link_flags[index]+=',_th14_async_invoke,_th14_async_frame'
    commands=[('compile',[sys.executable,str(emcc),*base['flags'],'-c',str(source/app_name),'-o',str(obj)]),
              ('link',[sys.executable,str(emcc),*base['flags'],*[str(x)for x in inputs],*link_flags,'-o',str(out/'th14-sdl.mjs')])]
    (out/'run-tool.py').write_bytes(Path(__file__).read_bytes());(out/'argv.json').write_text(json.dumps(commands,indent=2)+'\n')
    for label,argv in commands:
        with(out/(label+'.log')).open('wb')as f:p=subprocess.run(argv,cwd=source/'th12_web',env=env,stdout=f,stderr=subprocess.STDOUT,timeout=240)
        assert p.returncode==0,(label,p.returncode,(out/(label+'.log')).read_text()[-4000:])
    (out/'Th14AsyncRuntime.mjs').write_bytes((source/'portable/sdl/Th14AsyncRuntime.mjs').read_bytes())
    for name in base.get('archiveWorkerFiles',{}):
        old=BASE/name
        if old.exists():os.link(old,out/name)
    build=dict(base);build.update(sourceBindings=inventory,compiledUnits=1,reusedObjectCount=145,reusedObjectHashes=reused,
        reuseBuildReportSha256=SHA(base_raw),exports=base['exports']+['th14_async_invoke','th14_async_frame'],linkFlags=link_flags,
        objectHashes={**base['objectHashes'],app_name:SHA(obj.read_bytes())},frameAndWorkerCallbacksSerialized=True,
        wasmBytes=(out/'th14-sdl.wasm').stat().st_size,wasmSha256=SHA((out/'th14-sdl.wasm').read_bytes()),loaderSha256=SHA((out/'th14-sdl.mjs').read_bytes()),
        toolSha256=SHA(Path(__file__).read_bytes()),sourceFileHardLinksImmutable=True,gameCoreObjectsReused=141,
        callbackSchedulingChanged=True,browserRun=False,browserAcceptance=False,completeGame=False)
    (out/'build.json').write_text(json.dumps(build,indent=2)+'\n')
    print(json.dumps({k:build[k]for k in ['compiledUnits','reusedObjectCount','wasmSha256','completeGame']}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
    assert out.is_relative_to(R/'artifacts/th14')and not out.exists();main(out)
