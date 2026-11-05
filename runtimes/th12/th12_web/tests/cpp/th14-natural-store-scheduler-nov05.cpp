// Diagnostic host delivery only. The real production ReplayRngRestoreJobTh14
// performs every store and the real GameSession copies its own replay entry.
#include "th14-shot-lifetime-observer-nov05.cpp"
namespace natural_store_scheduler {
struct Effects final:StageResourceEffects {
 StageResourceEffects* next=nullptr;
 u32 target=0,callback=0,owner=0,object=0,primitive=0,animation=0,next_primitive=0,next_animation=0;
 u32 file=0,script=0,released=0,rng_visits=0,negative_before_read=0;
 bool failed=false,installed=false,snapshot_observed=false,finished=false;
 u64 times[4]{};const AnmVm* active=nullptr;const AnmVm* following=nullptr;
 std::function<bool(const AnmVm&,Rng&,RngBoundary)> previous_rng;
 StageObjectVmBoundaryTh14 previous_object;
 std::function<bool(const AnmVm&)> previous_initial;
 std::unique_ptr<ReplayRngRestoreScopeTh14> observation;
 u32 observations[4][12]{};u32 count=0;
 bool prepare(StageResources& s)override{return next->prepare(s);}
 bool core_ready()const override{return next->core_ready();}
 bool stage_ready()const override{return next->stage_ready();}
 bool defer_initial_stage_decode()const override{return next->defer_initial_stage_decode();}
 bool begin_stage_worker_wait(bool initial)override{return next->begin_stage_worker_wait(initial);}
 bool stage_worker_wait_ready()const override{return next->stage_worker_wait_ready();}
 bool draw_startup_loading()override{return next->draw_startup_loading();}
 bool defer_ending_loading()const override{return next->defer_ending_loading();}
 bool begin_ending_loading()override{return next->begin_ending_loading();}
 void finish_ending_loading()override{next->finish_ending_loading();}
 DialogueEffects* dialogue_text_device()override{return next->dialogue_text_device();}
 void release(StageResources& s)override{next->release(s);}
 bool prepare_animation(AnmResource& a)override{return next->prepare_animation(a);}
 bool prepare_manual_image(AnmResource& a,u32 i,const u8* p,u32 n)override{return next->prepare_manual_image(a,i,p,n);}
 void release_animation(AnmResource& a)override{next->release_animation(a);}
 bool read_replay(const std::string& name,std::vector<u8>& out)override{return next->read_replay(name,out);}
 const std::string& last_error()const override{return next->last_error();}
 DecodeResult decode_stage_phase(GameResources& r,StageResources& s,Phase p,u32 c)override{return next->decode_stage_phase(r,s,p,c);}
 void cancel_stage_decode(StageResources& s)override{next->cancel_stage_decode(s);}
 bool prepare_stage_phase(StageResources& s,Phase p)override{return next->prepare_stage_phase(s,p);}
 bool stage_phase_ready(Phase p)const override{return next->stage_phase_ready(p);}
 void cancel_stage_phases(StageResources& s,u32 mask)override{next->cancel_stage_phases(s,mask);}
 void finish_stage_phases(StageResources& s,u32 mask)override{next->finish_stage_phases(s,mask);}
 ReplayRngRestoreResultTh14 stage_rng_store_readiness(ReplayRngRestorePointTh14 point)const override{
  if(session.state.stage!=target)return next->stage_rng_store_readiness(point);
  using P=ReplayRngRestorePointTh14;using R=ReplayRngRestoreResultTh14;
  const u32 bit=point==P::GameplaySeedStored?1:point==P::ScriptSeedStored?2:point==P::GameplayCounterCleared?4:0;
  if(!bit||failed)return R::Failed;
  return released&bit?R::Ready:R::Waiting;
 }
 ReplayRngRestoreResultTh14 stage_replay_snapshot_readiness()const override{
  if(session.state.stage!=target)return next->stage_replay_snapshot_readiness();
  if(failed)return ReplayRngRestoreResultTh14::Failed;
  return released&8?ReplayRngRestoreResultTh14::Ready:ReplayRngRestoreResultTh14::Waiting;
 }
 bool advance(u32 index){
  const u32 expected=(1u<<index)-1;
  if(failed||index>3||released!=expected||probe_clock_ns>times[index]){failed=true;return false;}
  probe_clock_ns=times[index];released|=1u<<index;return true;
 }
 void record(u32 point){
  if(count>=4){failed=true;return;}
  auto& game=session.animations.visual_rng;auto& random=session.animations.script_rng;
  const u32 values[]={point,public_player_observations,session.state.stage,
   random.seed,random.calls,game.seed,game.calls,released,u32(probe_clock_ns),u32(probe_clock_ns>>32),
   session.battle?u32(session.battle->stage_initialization_finished):0,u32(count)};
  for(u32 i=0;i<12;++i)observations[count][i]=values[i];++count;
 }
} effects;
}
API(natural_store_configure) u32 natural_store_configure(u32 stage,u32 callback,u32 owner,u32 object,
 u32 primitive,u32 animation,u32 next_primitive,u32 next_animation,u32 file,u32 script,
 u64 game_ns,u64 script_ns,u64 counter_ns,u64 snapshot_ns,u32 negative_before_read){
 using namespace natural_store_scheduler;auto& e=effects;
 if(e.installed||public_player_observations!=1||!session.battle||!session.resources.effects||
    stage<2||stage>6||!callback||negative_before_read>1||
    !(probe_clock_ns<=game_ns&&game_ns<script_ns&&script_ns<counter_ns&&counter_ns<snapshot_ns))return 0;
 if(!observed_worker_initialize(stage,game_ns))return 0;
 e.target=stage;e.callback=callback;e.owner=owner;e.object=object;e.primitive=primitive;e.animation=animation;
 e.next_primitive=next_primitive;e.next_animation=next_animation;e.file=file;e.script=script;
 e.times[0]=game_ns;e.times[1]=script_ns;e.times[2]=counter_ns;e.times[3]=snapshot_ns;e.negative_before_read=negative_before_read;
 e.next=session.resources.effects;session.resources.effects=&e;e.installed=true;
 e.previous_object=session.stage_load_object_boundary;
 session.stage_load_object_boundary=[](const Stage& owner,const AnmVm& vm,u32 object,u32 primitive,u32 animation,AnmManager::VmBoundaryTh14 point){
  auto& e=effects;
  if(e.previous_object&&!e.previous_object(owner,vm,object,primitive,animation,point))return false;
  if(e.finished)return true;
  if(session.state.stage!=e.target||public_player_observations!=e.callback||
     u32(owner.state.stage_number)!=e.owner||object!=e.object)return !e.failed;
  if(primitive==e.primitive&&animation==e.animation){
   if(vm.file_index!=e.file||u32(vm.script_index)!=e.script){e.failed=true;return false;}
   if(point==AnmManager::VmBoundaryTh14::BeforeCall){e.active=&vm;if(!e.advance(0))return false;}
   else{if(e.active!=&vm||!e.advance(2))return false;e.active=nullptr;}
  }else if(primitive==e.next_primitive&&animation==e.next_animation&&point==AnmManager::VmBoundaryTh14::BeforeCall){
   e.following=&vm;if(!e.advance(3))return false;
  }
  return !e.failed;
 };
 e.previous_rng=session.animations.before_rng_boundary;
 session.animations.before_rng_boundary=[](const AnmVm& vm,Rng& rng,RngBoundary point){
  auto& e=effects;
  if(e.previous_rng&&!e.previous_rng(vm,rng,point))return false;
  if(e.finished)return true;
  const auto chosen=e.negative_before_read?RngBoundary::BeforeRead:RngBoundary::SeedRead;
  if(session.state.stage==e.target&&public_player_observations==e.callback&&
     &vm==e.active&&&rng==&session.animations.script_rng&&point==chosen){
   ++e.rng_visits;if(e.rng_visits!=1||!e.advance(1))return false;
  }
  return !e.failed;
 };
 e.previous_initial=session.animations.before_initial_update;
 session.animations.before_initial_update=[](const AnmVm& vm){
  auto& e=effects;
  if(e.previous_initial&&!e.previous_initial(vm))return false;
  if(e.finished)return true;
  if(!e.snapshot_observed&&&vm==e.following&&session.battle&&session.battle->stage_initialization_finished){
   e.snapshot_observed=true;e.record(3);
  }
  return !e.failed;
 };
 e.observation=std::make_unique<ReplayRngRestoreScopeTh14>(session.animations.visual_rng,&e,
  [](void* owner,ReplayRngRestorePointTh14 point,Rng&,Rng*){
   auto& e=*static_cast<Effects*>(owner);if(session.state.stage!=e.target)return;
   using P=ReplayRngRestorePointTh14;
   const u32 at=point==P::GameplaySeedStored?0:point==P::ScriptSeedStored?1:point==P::GameplayCounterCleared?2:~0u;
   if(at>2){e.failed=true;return;}e.record(at);
  });
 return 1;
}
API(natural_store_state) u32 natural_store_state(u32 index){
 const auto& e=natural_store_scheduler::effects;
 const u32 values[]={u32(e.installed),u32(e.failed),e.released,e.count,e.rng_visits,
  u32(e.snapshot_observed),u32(session.resources.effects==&e),u32(e.active!=nullptr)};
 return index<8?values[index]:~0u;
}
API(natural_store_observation) u32 natural_store_observation(u32 row,u32 word){
 const auto& e=natural_store_scheduler::effects;return row<e.count&&word<12?e.observations[row][word]:~0u;
}
API(natural_store_finish) u32 natural_store_finish(){
 using namespace natural_store_scheduler;auto& e=effects;
 if(!e.installed||e.failed||e.released!=15||e.count!=4||e.rng_visits!=1||
    !e.snapshot_observed||e.active||session.resources.effects!=&e)return 0;
 // A subsequently installed read-only auditor can wrap our callback. Leave
 // that chain transparent instead of replacing somebody else's top callback.
 e.observation.reset();session.resources.effects=e.next;e.finished=true;
 return !ReplayRngRestoreScopeTh14::active&&session.resources.effects==e.next;
}
