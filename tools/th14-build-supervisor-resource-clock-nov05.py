"""Add one clock-only observer call at the frozen Supervisor loader-pump site.

Production sources stay untouched; only the diagnostic GameSession object is
recompiled, and 140 hash-checked engine objects are reused. The additional
fixture supplies declared boundary times, never original gameplay values.
"""
from pathlib import Path
import argparse,hashlib,json,os,re,subprocess
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()
BASE=R/'artifacts/th14/script-rng-read-generation-nov05/portable-audit-build/observer-build.json'
def main(out):
    assert not out.exists();out.mkdir(parents=True);objects=out/'objects';objects.mkdir()
    raw=BASE.read_bytes();base=json.loads(raw);old_source=Path(base['sourceSnapshotRoot'])
    assert SHA((BASE.parent/'observer.wasm').read_bytes())==base['wasmSha256']=='b129d06717e7e09f0d5fa4e8090993bc3177c88fa74bbc77fa254a52580eefef'
    for row in base['objectBindings']:assert SHA(Path(row['path']).read_bytes())==row['sha256']
    for name,digest in {**base['sourceHashes'],**base['headerHashes']}.items():assert SHA((old_source/name).read_bytes())==digest
    source=out/'source';name='th12_web/cpp/game/GameSession.cpp'
    for path in old_source.rglob('*'):
        if not path.is_file():continue
        relative=path.relative_to(old_source)
        assert path.suffix in ['.cpp','.hpp','.h','.inc','.wgsl']and path.stat().st_size<5000000,str(relative)
        if relative.as_posix()==name:continue
        target=source/relative;target.parent.mkdir(parents=True,exist_ok=True);os.link(path,target)
    original=(old_source/name).read_bytes();text=original.decode().replace('\r\n','\n')
    first='#include "GameSession.hpp"';assert text.count(first)==1
    text=text.replace(first,first+'\nextern "C" bool th14_observer_supervisor_resource_pump_clock();')
    needle='''        // graphics upload readiness is a separate resource phase boundary.
        if(!battle->pump_stage_loading(stage_load_clock(),animations.first_deferred_capture_file_index(),stage_load_host_flags))return fail(battle->error.c_str());'''
    assert text.count(needle)==1
    text=text.replace(needle,needle.split('\n')[0]+'''
        if(!th14_observer_supervisor_resource_pump_clock())return fail("Observer Supervisor resource-pump clock failed");
        if(!battle->pump_stage_loading(stage_load_clock(),animations.first_deferred_capture_file_index(),stage_load_host_flags))return fail(battle->error.c_str());''')
    patched=source/name;patched.write_text(text,encoding='utf8',newline='\n')
    fixture=R/'runtimes/th12/th12_web/tests/cpp/th14-supervisor-resource-clock-fixture-nov05.cpp';frozen=out/'fixture-source.cpp';frozen.write_bytes(fixture.read_bytes())
    include=[source/'th12_web/cpp/game',source/'th12_web/cpp/sdl',fixture.parent]
    flags=[x for x in base['flags']if not x.startswith('-I')]+['-I'+str(x)for x in include]
    compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert SHA(compiler.read_bytes())==base['compilerSha256']
    env={**os.environ,'TEMP':str(objects),'TMP':str(objects)};obj=objects/'GameSession.cpp.o'
    reused=[row for row in base['objectBindings']if Path(row['path']).name!='GameSession.cpp.o'];assert len(reused)==140
    bindings=[dict(path=str(obj),sha256=None)if Path(row['path']).name=='GameSession.cpp.o'else row for row in base['objectBindings']]
    commands=[('compile',[str(compiler),*flags,'-c',str(patched),'-o',str(obj)]),
        ('link',[str(compiler),*flags,*base['linkFlags'],str(frozen),*[row['path']for row in bindings],'-o',str(out/'observer.wasm')])]
    for label,argv in commands:
        (out/(label+'-argv.json')).write_text(json.dumps(argv,indent=2)+'\n')
        p=subprocess.run(argv,cwd=R,env=env,capture_output=True,timeout=180);(out/(label+'.log')).write_bytes(p.stdout+p.stderr)
        assert p.returncode==0,p.stderr.decode(errors='replace')[-3000:]
    for row in bindings:
        if row['sha256']is None:row['sha256']=SHA(obj.read_bytes())
    dependencies={}
    def scan(path):
        path=path.resolve();key=path.as_posix()
        if key in dependencies:return
        data=path.read_bytes();dependencies[key]=SHA(data)
        for quoted in re.findall(r'^\s*#\s*include\s*"([^"]+)"',data.decode(),re.M):
            child=next((p for p in [path.parent/quoted,*[d/quoted for d in include]]if p.exists()),None);assert child,quoted;scan(child)
    scan(frozen)
    hashes={**base['sourceHashes'],name:SHA(patched.read_bytes())}
    report=dict(base);report.update(sourceHashes=hashes,sourceSnapshotRoot=str(source),objectBindings=bindings,flags=flags,
        fixtureGraphRoot=str(frozen),expandedFixtureSha256=SHA(frozen.read_bytes()),fixtureDependencyHashes=dependencies,
        wasmSha256=SHA((out/'observer.wasm').read_bytes()),baseBuildSha256=SHA(raw),buildToolSha256=SHA(Path(__file__).read_bytes()),
        engineSourcesRecompiledForThisLink=1,engineObjectsReusedForThisLink=140,clockOnlySupervisorPumpObservationCallAdded=True,
        originalGameSessionSourceSha256=SHA(original),diagnosticGameSessionSourceSha256=SHA(patched.read_bytes()),
        rootProductionSourcesModified=False,originalStateValuesProvidedToEngine=False,ordinaryIndependentTimingAccepted=False,completeGame=False)
    (out/'observer-build.json').write_text(json.dumps(report,indent=2)+'\n');(out/'build-tool.py').write_bytes(Path(__file__).read_bytes())
    assert SHA((old_source/name).read_bytes())==SHA(original)
    print(json.dumps({k:report[k]for k in ['compiled','wasmSha256','engineSourcesRecompiledForThisLink','engineObjectsReusedForThisLink','rootProductionSourcesModified']}))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
    assert out.is_relative_to(R/'artifacts/th14')and not out.exists();main(out)
