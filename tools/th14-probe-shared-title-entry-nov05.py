"""Relink an actual title-to-attract entry probe over the fresh 141-unit core."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];B=R/'artifacts/th14/shared-scene-copy-nov05/session-build'
SHA=lambda raw:hashlib.sha256(raw).hexdigest()
def main(out):
 out=out.resolve();assert out.is_relative_to(R/'artifacts/th14')and not out.exists();out.mkdir(parents=True)
 build_raw=(B/'build.json').read_bytes();b=json.loads(build_raw)
 assert b['compiled']and b['gameUnitsRecompiled']==141
 fixture=(B/'fixture.cpp').read_bytes();assert SHA(fixture)==b['fixtureSha256']
 append=r'''
namespace {u32 title_probe[12]{};}
API(probe_title_entry) u32 probe_title_entry(u32 ticks,u32 cookie,u32 geometry_frame){
 if(game||!NativeStackTh14::preinitialized_cookie(cookie))return 0;
 game=std::make_unique<GameSession>(ticks);game->animations.th14_native_stack.configure(cookie,geometry_frame);
 game->stage_load_clock=clock_ns;game->resources.effects=&effects;game->interactive=false;
 title_probe[0]=game->animations.script_rng.calls;
 if(!game->open_title(source,true))return 0;
 title_probe[1]=game->animations.script_rng.calls;
 u32 updates=0;
 for(;updates<4000&&game->state.phase==GameSessionPhase::title;++updates){
  if(!game->update({0})||!game->draw(renderer))return 0;
 }
 title_probe[2]=updates;title_probe[3]=u32(game->state.phase);title_probe[4]=game->state.stage;
 title_probe[5]=game->animations.script_rng.calls;title_probe[6]=game->animations.script_rng.seed;
 title_probe[7]=game->state.demo?1:0;title_probe[8]=callbacks;
 if(game->battle){
  // Same one-time attract-case initialization already declared in the native
  // reference. No RNG, state words or per-frame inputs are replaced.
  game->state.demo=false;game->battle->before_player_update=capture;
  rows.clear();if(!game->update({0})||!game->draw(renderer))return 0;
  title_probe[9]=callbacks;title_probe[10]=game->animations.script_rng.calls;
 }
 return game->battle?1:0;
}
API(title_probe_value) u32 title_probe_value(u32 index){return index<12?title_probe[index]:~0u;}
'''
 app_path=B/'source/th12_web/cpp/sdl/Application.cpp'
 app=app_path.read_text(encoding='utf8');needle='bool draw_startup_loading()override{'
 start=app.index(needle);opening=start+len(needle)-1;depth=1;end=opening+1
 while depth:
  if app[end]=='{':depth+=1
  elif app[end]=='}':depth-=1
  end+=1
 draw_method=app[start:end]
 loading=r'''
#include "LoadingTh14.hpp"
namespace {
struct LoadingPrelude final:StageResourceEffects {
 GameSession& session;
 struct {std::string error;}graphics;
 AnmResource boot_signature;LoadingTh14 boot_loading;
 bool ready=false,boot_signature_active=true,boot_signature_uploaded=true,boot_signature_pending=true;
 bool boot_ascii_uploaded=true,boot_ascii_pending=true;
 u32 boot_signature_handle=0,boot_signature_draws=0;
 explicit LoadingPrelude(GameSession& s):session(s){}
 bool core_ready()const override{return ready;}
 const std::string& last_error()const override{return graphics.error;}
 @DRAW@
};
}
static u32 run_loading_entry(u32 ticks,u32 cookie,u32 geometry_frame,bool queued){
 if(game||!NativeStackTh14::preinitialized_cookie(cookie))return 0;
 game=std::make_unique<GameSession>(ticks);game->animations.th14_native_stack.configure(cookie,geometry_frame);
 game->stage_load_clock=clock_ns;LoadingPrelude loading(*game);game->resources.effects=&loading;
 title_probe[0]=game->animations.script_rng.calls;
 if(!source.open_anm("sig.anm",loading.boot_signature)||!game->animations.prepare_resource(loading.boot_signature,1))return 0;
 if(!game->open_title(source,true))return 0;
 if(!queued){
  if(!game->compositor.initialize(game->resources.core.text))return 0;
  game->compositor.reset_cameras(false);
 }
 struct Upload {AnmResource* resource;u16 file;u32 chunk=0;};
 auto& core=game->resources.core;
 std::vector<Upload> uploads={{&loading.boot_signature,1},{&core.ascii,2},{&core.text,0},
  {&core.front,5},{&core.bullet,7},{&core.effect,8},{&core.title,16},{&core.title_variant,17}};
 u32 upload=queued?0:u32(uploads.size());
 if(queued)loading.boot_signature_uploaded=loading.boot_ascii_uploaded=false;
 title_probe[1]=game->animations.script_rng.calls;
 // Declared CPU-only ready control: both parsed bootstrap resources are
 // available before first draw. The actual draw callback owns the180 limit.
 while(loading.boot_signature_draws<180||upload<uploads.size()){
  if(upload<uploads.size()){
   if(upload>=3){constexpr u32 jobs[]={0,1,2,4,5};if(!game->resources.load_core_job(jobs[upload-3]))return 0;}
   auto& job=uploads[upload];TextureImage image;
   if(!job.resource->textures.empty()&&(job.chunk>=job.resource->textures.size()||!image.load(job.resource->textures[job.chunk])))return 0;
   if(++job.chunk>=job.resource->textures.size()){
    if(!game->animations.prepare_resource(*job.resource,job.file))return 0;
    if(job.file==1)loading.boot_signature_uploaded=true;
    if(job.file==2)loading.boot_ascii_uploaded=true;
    if(job.file==0){if(!game->compositor.initialize(core.text))return 0;game->compositor.reset_cameras(false);}
    ++upload;
   }
  }
  if(!game->animations.update(true)||!game->animations.update(false)||!game->draw(renderer))return 0;
 }
 game->animations.retire_resource(loading.boot_signature);loading.ready=true;
 if(!game->finish_loading())return 0;
 loading.boot_loading.finish(game->animations);
 if(!game->update({0}))return 0;
 if(game->animations.references(loading.boot_signature))return 0;
 loading.boot_signature_active=false;game->resources.effects=&effects;
 u32 updates=1;
 for(;updates<4000&&game->state.phase==GameSessionPhase::title;++updates){
  if(!game->update({0})||!game->draw(renderer))return 0;
 }
 title_probe[2]=updates;title_probe[3]=u32(game->state.phase);title_probe[4]=game->state.stage;
 title_probe[5]=game->animations.script_rng.calls;title_probe[6]=game->animations.script_rng.seed;
 title_probe[7]=game->state.demo?1:0;title_probe[8]=callbacks;
 if(game->battle){
  game->state.demo=false;game->interactive=false;game->battle->before_player_update=capture;
  rows.clear();if(!game->update({0})||!game->draw(renderer))return 0;
  title_probe[9]=callbacks;title_probe[10]=game->animations.script_rng.calls;
 }
 return game->battle?1:0;
}
API(probe_loading_entry) u32 probe_loading_entry(u32 ticks,u32 cookie,u32 geometry_frame){return run_loading_entry(ticks,cookie,geometry_frame,false);}
API(probe_queued_loading_entry) u32 probe_queued_loading_entry(u32 ticks,u32 cookie,u32 geometry_frame){return run_loading_entry(ticks,cookie,geometry_frame,true);}
'''.replace('@DRAW@',draw_method)
 frozen=out/'fixture.cpp';frozen.write_bytes(fixture+append.encode()+loading.encode())
 objects=[]
 for name,digest in b['objectHashes'].items():
  path=B/'objects'/(name.replace('/','_')+'.o');assert SHA(path.read_bytes())==digest;objects.append(path)
 compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
 argv=[str(compiler),*b['flags'],*b['linkFlags'],str(frozen),*[str(p)for p in objects],'-o',str(out/'probe.wasm')]
 with(out/'compile.log').open('wb')as log:
  result=subprocess.run(argv,cwd=R,env={**os.environ,'TEMP':str(out),'TMP':str(out)},stdout=log,stderr=subprocess.STDOUT,timeout=120)
 assert result.returncode==0,'Retain compile.log'
 for name in b['sharedSceneModuleFiles']:(out/name).write_bytes((B/name).read_bytes())
 report=dict(compiled=True,gameObjectsReused=141,baseBuildSha256=SHA(build_raw),sharedWasmMemory=True,sharedMemory=b['sharedMemory'],sharedSceneModuleFiles=b['sharedSceneModuleFiles'],
  parentFullSessionBuildPath=(B/'build.json').relative_to(R).as_posix(),parentGlesBuildSha256=b['parentGlesBuildSha256'],
  wasmSha256=SHA((out/'probe.wasm').read_bytes()),fixtureSha256=SHA(frozen.read_bytes()),
  toolSha256=SHA(Path(__file__).read_bytes()),actualGameSessionTitleAndAttractPath=True,
  actualSdlStartupDrawMethodSha256=SHA(draw_method.encode()),sdlApplicationSha256=SHA(app_path.read_bytes()),
  syntheticClockReadyOrVmTargetsUsed=False,ordinaryColdApplicationReproduced=False,queuedCpuBootstrapAvailable=True,completeGame=False)
 (out/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(compiled=True,gameObjectsReused=141)))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);main(p.parse_args().output)
