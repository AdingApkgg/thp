"""Recompile only Renderer over the hash-bound working TH14 async GLES build."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys
R=Path(__file__).resolve().parents[1]
BASE=R/'artifacts/th14/browser-ordinary-gles-nov05/async-build-retry1'
OLD=R/'artifacts/th14/gles-clip-portable-nov04/browser-gles-nov05'
SHA=lambda data:hashlib.sha256(data).hexdigest()

def main(out):
    assert not out.exists();out.mkdir(parents=True);objects=out/'objects';objects.mkdir()
    base_raw=(BASE/'build.json').read_bytes();base=json.loads(base_raw)
    assert base['wasmSha256']=='4a8e02cc5d27c6fe13c3948fe750f9050d2a941421056a3f5b12bf745eedeca9'
    assert base['backend']=='gles'and base['frameAndWorkerCallbacksSerialized']
    name='portable/sdl/Renderer.cpp';source=out/'source';inventory=dict(base['sourceBindings'])
    for path,row in inventory.items():assert SHA((BASE/'source'/path).read_bytes())==row['sha256'],path
    for path in (BASE/'source').rglob('*'):
        if not path.is_file():continue
        dest=source/path.relative_to(BASE/'source');dest.parent.mkdir(parents=True,exist_ok=True)
        if path.relative_to(BASE/'source').as_posix()==name:
            raw=(R/'runtimes/th12'/name).read_bytes();dest.write_bytes(raw)
            inventory[name]=dict(bytes=len(raw),sha256=SHA(raw),origin='th14-raf-owned-swap')
        else:os.link(path,dest)
    # Prove that the accepted change consists solely of the timing ownership guard.
    before=(BASE/'source'/name).read_text();after=(source/name).read_text()
    old='context=SDL_GL_CreateContext(window);if(!context){failure=SDL_GetError();return false;}SDL_GL_SetSwapInterval(1);drawState=DrawStateCache{};'
    new='''context=SDL_GL_CreateContext(window);if(!context){failure=SDL_GetError();return false;}
#if !defined(__EMSCRIPTEN__) || !defined(PORT_TITLE) || PORT_TITLE != 14
 SDL_GL_SetSwapInterval(1);
#endif
 // TH14's Asyncify-safe host owns requestAnimationFrame scheduling. SDL's
 // Emscripten swap interval instead configures emscripten_set_main_loop,
 // which this host never creates; its deferred first-pump call would fail.
 drawState=DrawStateCache{};'''
    assert before.count(old)==1 and before.replace(old,new)==after
    obj=objects/(name.replace('/','_')+'.o');inputs=[];reuse={};origins={}
    for unit,digest in base['objectHashes'].items():
        if unit==name:inputs.append(obj);continue
        choices=[home/'objects'/(unit.replace('/','_')+'.o') for home in (BASE,OLD)]
        original=next(path for path in choices if path.is_file()and SHA(path.read_bytes())==digest)
        inputs.append(original);reuse[unit]=digest;origins[unit]=original.relative_to(R).as_posix()
    assert len(inputs)==146 and len(reuse)==145
    sdk=R/'runtimes/th12/tools/emsdk';emcc=sdk/'upstream/emscripten/emcc.py'
    env={**os.environ,'EM_CONFIG':str(sdk/'.emscripten'),'EMSDK':str(sdk),'EMSDK_PYTHON':sys.executable,
        'EMCC_CORES':'2','TEMP':str(objects),'TMP':str(objects),'TMPDIR':str(objects)}
    commands=[('compile',[sys.executable,str(emcc),*base['flags'],'-c',str(source/name),'-o',str(obj)]),
        ('link',[sys.executable,str(emcc),*base['flags'],*[str(path)for path in inputs],*base['linkFlags'],'-o',str(out/'th14-sdl.mjs')])]
    (out/'argv.json').write_text(json.dumps(commands,indent=2)+'\n')
    for label,argv in commands:
        with(out/(label+'.log')).open('wb')as log:
            result=subprocess.run(argv,cwd=source/'th12_web',env=env,stdout=log,stderr=subprocess.STDOUT,timeout=240)
        assert result.returncode==0,(label,(out/(label+'.log')).read_text()[-4000:])
    for filename in ['Th14AsyncRuntime.mjs',*base.get('archiveWorkerFiles',{})]:
        if(BASE/filename).is_file():os.link(BASE/filename,out/filename)
    report=dict(base);report.update(sourceBindings=inventory,compiledUnits=1,reusedObjectCount=145,
        reusedObjectHashes=reuse,reusedObjectPaths=origins,reuseBuildReportSha256=SHA(base_raw),
        objectHashes={**base['objectHashes'],name:SHA(obj.read_bytes())},
        wasmBytes=(out/'th14-sdl.wasm').stat().st_size,wasmSha256=SHA((out/'th14-sdl.wasm').read_bytes()),
        loaderSha256=SHA((out/'th14-sdl.mjs').read_bytes()),toolSha256=SHA(Path(__file__).read_bytes()),
        gameCoreObjectsReused=141,rendererOnlyChanged=True,rafOwnsTiming=True,
        browserRun=False,browserAcceptance=False,completeGame=False)
    (out/'build.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({key:report[key]for key in ['compiledUnits','reusedObjectCount','wasmSha256','completeGame']}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14');main(out)
