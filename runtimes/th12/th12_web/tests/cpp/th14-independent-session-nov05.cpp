// Full GameSession, real parser/update/draw/loader, declared CPU-only device.
// No observed frame/VM schedules or original state values are replayed here.
#include "GameSession.hpp"
#include "TextureImage.hpp"
#include "StageUploadsTh14.hpp"
#include "StageWorkerWaitTh14.hpp"
#include "FrameCadence.hpp"
#include <cstdlib>
#include <cstring>
#include <vector>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
#define IMPORT(name) __attribute__((import_module("stagehost"),import_name(#name)))
extern "C" IMPORT(now_ms) double now_ms();
extern "C" IMPORT(request_begin) u32 request_begin(u32,u32);
extern "C" IMPORT(ready) u32 ready(u32);
extern "C" IMPORT(committed) u32 committed(u32);
extern "C" IMPORT(cancel) void cancel();
namespace {
GameResources source;
std::unique_ptr<GameSession> game;
u32 callbacks=0,draws=0;
constexpr u32 stride=114;
std::vector<u32> rows,events;
touhou::sdl::FrameCadence cadence;
u64 clock_ns(){return u64(now_ms()*1000000.);}
void event(u32 kind,u32 generation,u32 detail){
 const auto ns=clock_ns();const auto& a=game->animations;
 const u32 values[]={kind,game->state.stage,generation,detail,a.visual_rng.seed,a.visual_rng.calls,
  a.script_rng.seed,a.script_rng.calls,u32(ns),u32(ns>>32),callbacks,game->battle?u32(game->battle->stage_initialization_finished):0};
 events.insert(events.end(),std::begin(values),std::end(values));
}
struct Graphics final:ZunGraphics {
 touhou::graphics::PipelineState state;u32 submissions=0;
 touhou::graphics::PipelineState& pipeline()override{return state;}
 u32 texture(const AnmResource&,u32 index)override{return index+1;}
 void bind_texture(u32)override{}
 void set_layout(touhou::graphics::VertexLayout)override{}
 void set_matrix(touhou::graphics::MatrixKind,const Matrix4&)override{}
 void triangles(u32,const void*,u32)override{++submissions;}
 void primitives(touhou::graphics::Topology,u32,const void*,u32)override{++submissions;}
 bool select_target(const AnmResource*,u32)override{return true;}
 bool clear_target(u32,const GraphicsViewport*,u32)override{return true;}
} graphics;
AnmRenderer renderer{graphics};
struct Effects final:StageResourceEffects {
 th11::sdl::StageUploadsTh14 uploads;
 th11::sdl::StageWorkerWaitTh14 wait;
 std::string failure;
 bool begin_stage_worker_wait(bool initial)override{
  cancel();wait.begin(initial);
  if(initial)return true;
  event(1,u32(wait.generation),0);
  return request_begin(u32(wait.generation),game->state.replay?1:0)!=0;
 }
 bool stage_worker_wait_ready()const override{return wait.ready(clock_ns());}
 static u32 operation(ReplayRngRestorePointTh14 point){
  using P=ReplayRngRestorePointTh14;
  return point==P::GameplaySeedStored||point==P::StageSeedRecorded?0:point==P::ScriptSeedStored?1:2;
 }
 ReplayRngRestoreResultTh14 stage_rng_store_readiness(ReplayRngRestorePointTh14 p)const override{
  const auto code=ready(operation(p));return code==0?ReplayRngRestoreResultTh14::Waiting:
   code==1?ReplayRngRestoreResultTh14::Ready:ReplayRngRestoreResultTh14::Failed;
 }
 bool stage_rng_store_committed(ReplayRngRestorePointTh14 p)override{
  event(3,u32(wait.generation),operation(p));return committed(operation(p))!=0;
 }
 ReplayRngRestoreResultTh14 stage_replay_snapshot_readiness()const override{
  const auto code=ready(3);return code==0?ReplayRngRestoreResultTh14::Waiting:
   code==1?ReplayRngRestoreResultTh14::Ready:ReplayRngRestoreResultTh14::Failed;
 }
 bool stage_replay_snapshot_committed()override{event(4,u32(wait.generation),3);return committed(3)!=0;}
 bool prepare_stage_phase(StageResources& owner,Phase p)override{return uploads.begin(owner,p);}
 bool stage_phase_ready(Phase p)const override{return uploads.ready(p);}
 void finish_stage_phases(StageResources& owner,u32 mask)override{uploads.finish(owner);event(6,u32(wait.generation),mask);}
 void cancel_stage_phases(StageResources& owner,u32 mask)override{
  wait.cancel();cancel();uploads.cancel(owner);event(5,u32(wait.generation),mask);
 }
 void release(StageResources& owner)override{uploads.cancel(owner);}
 const std::string& last_error()const override{return failure;}
 bool pump(){
  return uploads.advance([&](const auto& job){
   if(job.resource->textures.empty()&&job.chunk==0)return true;
   TextureImage image;
   if(job.chunk>=job.resource->textures.size()||!image.load(job.resource->textures[job.chunk])){
    failure="CPU-only texture conversion failed: "+image.failure;return false;
   }
   return true;
  });
 }
} effects;
void capture(const GameBattle& b){
 ++callbacks;const auto& p=*b.player;const auto& e=b.economy;
 u32 live=0;for(u32 i=0;i<256;++i)if(p.shots.at(i).state)++live;
 const i32 selected[]={b.control_frame(),i32(p.input.movement.held),i32(p.input.movement.pressed),
  p.motion.state.x,p.motion.state.y,p.state.life_state,p.state.state_timer.current,
  p.state.transition_timer.current,p.state.th14_shooting_age.current,p.state.invincibility.current,
  p.shots.schedule.timer.current,p.motion.state.weapon_mode,e.score_units,e.graze,e.point_value,e.power,
  e.lives,e.life_fragments,e.th14_bombs,e.th14_bomb_fragments,e.rank,
  i32(b.animations.script_rng.seed),i32(b.animations.script_rng.calls),i32(b.animations.visual_rng.seed),
  i32(b.animations.visual_rng.calls),i32(b.enemies.count),i32(live),game->state.character,
  game->state.subtype,game->state.difficulty,i32(game->state.stage),i32(p.th14_scale.flags)};
 static_assert(sizeof(selected)==128);
 const auto start=rows.size();rows.push_back(callbacks);
 for(auto word:selected)rows.push_back(u32(word));
 const auto& c=game->compositor.world_camera;
 // Retail-order 75 words, the same public field mapping as SceneCameraReadJob.
 for(u32 i=0;i<75;++i){
  const auto offset=i<18?i*4:i<21?offsetof(SceneCamera,target_offset)+(i-18)*4:
   i==21?offsetof(SceneCamera,fov):i==22?offsetof(SceneCamera,render_width):
   i==23?offsetof(SceneCamera,render_height):offsetof(SceneCamera,view)+(i-24)*4;
  u32 word;std::memcpy(&word,reinterpret_cast<const u8*>(&c)+offset,4);rows.push_back(word);
 }
 rows.push_back(u32(b.hud.score.displayed));rows.push_back(u32(e.score_units));
 rows.push_back(game->playback.frame());rows.push_back(game->playback.callback_frame());
 rows.push_back(game->playback.selected_stage());
 const auto* entry=game->playback.stage(game->playback.selected_stage());rows.push_back(entry?entry->frames:0);
 if(rows.size()-start!=stride)game->error="full-session observation stride mismatch";
}
}
API(allocate) void* allocate(u32 count){return std::malloc(count);}
API(release) void release(void* value){std::free(value);}
API(open_archive) u32 open_archive(const u8* data,u32 size){return source.open_archive(data,size);}
API(begin_replay) u32 begin_replay(const u8* data,u32 size,u32 ticks,u32 cookie,u32 frame){
 if(game||!NativeStackTh14::preinitialized_cookie(cookie)||(frame&3u))return 0;
 game=std::make_unique<GameSession>(ticks);game->animations.th14_native_stack.configure(cookie,frame);
 game->stage_load_clock=clock_ns;game->resources.effects=&effects;game->interactive=false;
 if(!game->begin_replay(source,data,size,0,false))return 0;
 game->battle->before_player_update=capture;cadence.reset();return 1;
}
API(start_wait) u32 start_wait(u32 generation){
 if(!game||!effects.wait.owns(generation))return 0;
 if(!game->battle||!game->battle->pending_stage||!game->resources.loading_bundle()){
  effects.wait.cancel();cancel();return 0;
 }
 if(!effects.wait.start(generation,clock_ns()))return 0;
 event(2,generation,0);return 1;
}
API(finish_wait) u32 finish_wait(u32 generation){return effects.wait.finish(generation,clock_ns());}
API(frame) u32 frame(double seconds){
 if(!game)return 0;rows.clear();const auto ticks=cadence.advance(seconds);
 for(u32 i=0;i<ticks&&game->state.phase!=GameSessionPhase::finished;++i){
  if(!effects.pump()||!game->update({0})||!game->draw(renderer)||!game->sample_spell_clock(now_ms()/1000.))return 0;
  ++draws;
 }
 return game->error.empty()?1:0;
}
API(rows_data) const u32* rows_data(){return rows.data();}
API(rows_words) u32 rows_words(){return u32(rows.size());}
API(events_data) const u32* events_data(){return events.data();}
API(events_words) u32 events_words(){return u32(events.size());}
API(error) const char* error(){return game?game->error.c_str():source.error().c_str();}
API(meta) u32 meta(u32 n){
 if(!game)return ~0u;
 const auto* b=game->battle.get();
 const u32 values[]={u32(game->state.phase),game->state.stage,game->state.frame,callbacks,draws,
  b?u32(b->game_over_requested):0,b?u32(b->completion.state.exit):0,game->playback.stage_count(),
  game->playback.frame(),game->playback.callback_frame(),b?u32(b->pending_stage):0,
  g_th14_bullet_unhandled,g_th14_bullet_unsupported_native,u32(effects.wait.generation),
  effects.uploads.pending_count(),graphics.submissions};
 return n<16?values[n]:~0u;
}
API(stage_frames) u32 stage_frames(u32 number){const auto* value=game?game->playback.stage(number):nullptr;return value?value->frames:0;}
API(close_session) void close_session(){
 if(game){game->return_to_title();effects.wait.cancel();cancel();game.reset();}
}
