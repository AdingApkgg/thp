"""Recompile only Application with bounded loop prints; reuse145 GLES objects.

Diagnostic build only. Game logic, callback return expressions, input, renderer
and RNG are unchanged. No retail assets enter the source snapshot or build.
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
    assert base['backend']=='gles'and len(base['objectHashes'])==146
    source=out/'source';app_name='th12_web/cpp/sdl/Application.cpp'
    for path in (BASE/'source').rglob('*'):
        if not path.is_file():continue
        name=path.relative_to(BASE/'source').as_posix()
        if name==app_name:continue
        dest=source/name;dest.parent.mkdir(parents=True,exist_ok=True);os.link(path,dest)
    for name,item in base['sourceBindings'].items():assert SHA((BASE/'source'/name).read_bytes())==item['sha256']
    app_raw=(BASE/'source'/app_name).read_bytes();assert SHA(app_raw)=='c936a9ff4b0968c672c410adba3e49f8c35bbea67db47b2da08a289fc93eda62'
    s=app_raw.decode()
    def replace(a,b):
        nonlocal s
        assert s.count(a)==1,(a[:100],s.count(a));s=s.replace(a,b)
    replace('bool running=false,suspended=false;u32 loop_epoch=0;double previous_frame=-1;',
        'bool running=false,suspended=false;u32 loop_epoch=0;double previous_frame=-1;\nu32 loop_audit_entries=0;')
    replace('using namespace th11::sdl;running=false;++loop_epoch;',
        'using namespace th11::sdl;std::printf("[loop14] stop epoch=%u running=%u\\n",loop_epoch,unsigned(running));std::fflush(stdout);running=false;++loop_epoch;')
    replace('using namespace th11::sdl;if(running||!app.initialized)return;',
        'using namespace th11::sdl;std::printf("[loop14] start epoch=%u running=%u initialized=%u\\n",loop_epoch,unsigned(running),unsigned(app.initialized));std::fflush(stdout);if(running||!app.initialized)return;')
    replace('        if(!running||uintptr_t(epoch)!=loop_epoch)return EM_FALSE;',
        '        ++loop_audit_entries;if(loop_audit_entries<=6){std::printf("[loop14] entry n=%u epochArg=%u epoch=%u running=%u suspended=%u\\n",loop_audit_entries,unsigned(uintptr_t(epoch)),loop_epoch,unsigned(running),unsigned(suspended));std::fflush(stdout);}\n        if(!running||uintptr_t(epoch)!=loop_epoch)return EM_FALSE;')
    replace('        if(ticks)th11_browser_frame(ok?1:0,emscripten_get_now()-begin,ticks);',
        '''        if(loop_audit_entries<=6){std::printf("[loop14] before-bridge n=%u ticks=%u ok=%u running=%u phase=%u\\n",loop_audit_entries,ticks,unsigned(ok),unsigned(running),unsigned(app.session.state.phase));std::fflush(stdout);}
        if(ticks)th11_browser_frame(ok?1:0,emscripten_get_now()-begin,ticks);
        if(loop_audit_entries<=6){std::printf("[loop14] after-bridge n=%u running=%u epoch=%u\\n",loop_audit_entries,unsigned(running),loop_epoch);std::fflush(stdout);}''')
    replace('        if(!ok)running=false;return running?EM_TRUE:EM_FALSE;',
        '        if(!ok)running=false;if(loop_audit_entries<=6){std::printf("[loop14] native-return n=%u result=%u\\n",loop_audit_entries,unsigned(running?EM_TRUE:EM_FALSE));std::fflush(stdout);}return running?EM_TRUE:EM_FALSE;')
    app=source/app_name;app.parent.mkdir(parents=True,exist_ok=True);app.write_text(s,encoding='utf8',newline='\n')
    sdk=R/'runtimes/th12/tools/emsdk';emcc=sdk/'upstream/emscripten/emcc.py'
    env={**os.environ,'EM_CONFIG':str(sdk/'.emscripten'),'EMSDK':str(sdk),'EMSDK_PYTHON':sys.executable,'EMCC_CORES':'2',
        'TEMP':str(objects),'TMP':str(objects),'TMPDIR':str(objects)}
    app_object=objects/(app_name.replace('/','_')+'.o')
    compile_argv=[sys.executable,str(emcc),*base['flags'],'-c',str(app),'-o',str(app_object)]
    reused={};inputs=[]
    for name,digest in base['objectHashes'].items():
        if name==app_name:inputs.append(app_object);continue
        old=BASE/'objects'/(name.replace('/','_')+'.o');assert SHA(old.read_bytes())==digest
        inputs.append(old);reused[name]=digest
    assert len(inputs)==146 and len(reused)==145
    link_argv=[sys.executable,str(emcc),*base['flags'],*[str(x)for x in inputs],*base['linkFlags'],'-o',str(out/'th14-sdl.mjs')]
    (out/'run-tool.py').write_bytes(Path(__file__).read_bytes())
    (out/'argv.json').write_text(json.dumps([compile_argv,link_argv],indent=2)+'\n')
    for label,argv in [('compile',compile_argv),('link',link_argv)]:
        with(out/(label+'.log')).open('wb')as f:p=subprocess.run(argv,cwd=source/'th12_web',env=env,stdout=f,stderr=subprocess.STDOUT,timeout=240)
        assert p.returncode==0,(label,p.returncode)
    # Native archive helpers are unchanged aliases; no new worker compilation.
    for name in base.get('archiveWorkerFiles',{}):
        old=BASE/name
        if old.exists():os.link(old,out/name)
    build=dict(base);build['sourceBindings']=dict(base['sourceBindings']);build['sourceBindings'][app_name]=dict(bytes=app.stat().st_size,sha256=SHA(app.read_bytes()),origin='output-only-loop-audit')
    build['objectHashes']=dict(base['objectHashes']);build['objectHashes'][app_name]=SHA(app_object.read_bytes())
    build.update(compiledUnits=1,reusedObjectCount=145,reusedObjectHashes=reused,reuseBuildReportSha256=SHA(base_raw),
        wasmBytes=(out/'th14-sdl.wasm').stat().st_size,wasmSha256=SHA((out/'th14-sdl.wasm').read_bytes()),loaderSha256=SHA((out/'th14-sdl.mjs').read_bytes()),
        localLoopAuditOnly=True,productionGameplayChanged=False,sourceFileHardLinksImmutable=True,loopCallbackReturnExpressionUnchanged=True,
        toolSha256=SHA(Path(__file__).read_bytes()),browserRun=False,browserAcceptance=False,completeGame=False)
    (out/'build.json').write_text(json.dumps(build,indent=2)+'\n')
    print(json.dumps({k:build[k]for k in ['compiledUnits','reusedObjectCount','wasmSha256','localLoopAuditOnly','completeGame']}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
    assert out.is_relative_to(R/'artifacts/th14')and not out.exists();main(out)
