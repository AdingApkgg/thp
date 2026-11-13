from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];P=R/'artifacts/th14/ordinary-replay-menu-nov13/component';H=R/'artifacts/th14/native-viewer-application-nov13';H.mkdir(exist_ok=True);O=H/'component-v3';O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
j=load(P/'build.json')
for n,h in j['objectBindings'].items():assert sha(R/n)==h,n
s=(P/'fixture.cpp').read_text()+'''
API(viewer_ready) u32 viewer_ready(){return current->hosted_replay_open_ready();}
API(viewer_open) u32 viewer_open(const u8* p,u32 n,u32 stage){return current->open_hosted_replay(p,n,stage);}
API(viewer_status) const u32* viewer_status(){return current->hosted_replay_status();}
API(viewer_seek) i32 viewer_seek(u32 target,u32 budget){return current->hosted_replay_seek_step(target,budget);}
API(viewer_rate) u32 viewer_rate(double rate){return current->set_hosted_replay_rate(rate);}
API(viewer_close) void viewer_close(){current->close_hosted_replay();}
API(viewer_clock) u32 viewer_clock(double seconds){return current->hosted_cadence.advance(seconds,current->hosted_replay_rate);}
API(viewer_alloc) void* viewer_alloc(u32 size){return std::malloc(size);}
API(viewer_free) void viewer_free(void* p){std::free(p);}
API(viewer_describe) const char* viewer_describe(const u8* p,u32 n){static std::string result,error;return describe_replay_th14(p,n,result,error)?result.c_str():nullptr;}
'''
(O/'fixture.cpp').write_text(s,newline='\n');(O/'Th14WarmAttractCase.hpp').write_bytes((P/'Th14WarmAttractCase.hpp').read_bytes());cmd=[x.replace(str(P),str(O))for x in load(P/'command.json')];(O/'command.json').write_text(json.dumps(cmd,indent=2)+'\n')
with(O/'build.log').open('wb')as f:q=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=180,env=dict(os.environ,TEMP=str(O),TMP=str(O),TMPDIR=str(O)))
assert q.returncode==0,(O/'build.log').read_text(errors='replace')[-4000:]
bindings={n:sha(R/n)for n in j['sourceBindingsByMode']['candidate']if not n.startswith('artifacts/th14/ordinary-replay-menu-nov13/component/')}
for p in [O/'fixture.cpp',O/'Th14WarmAttractCase.hpp',R/'runtimes/th12/th12_web/cpp/game/ReplayDescriptionTh14.hpp',R/'runtimes/th12/portable/sdl/ReplayViewerClockTh14.hpp']:bindings[p.relative_to(R).as_posix()]=sha(p)
j.update(sourceBindingsByMode={'candidate':bindings},fixtureSha256=sha(O/'fixture.cpp'),outputs={'candidate':{'wasmSha256':sha(O/'candidate.wasm')}},nativeApplicationViewerMethods=True)
(O/'build.json').write_text(json.dumps(j,indent=2)+'\n');print(json.dumps(dict(compiled=True,wasmSha256=sha(O/'candidate.wasm'),normalProvidersReused=145)))
