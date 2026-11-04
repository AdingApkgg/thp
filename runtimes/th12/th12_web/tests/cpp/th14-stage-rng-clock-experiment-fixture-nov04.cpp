// Controlled host-clock experiment at a Stage object's existing callback.
// No RNG/health/input/geometry value is overwritten. This is not an observed
// timing adapter: the selected animation index is an explicit experiment.
#include "th14-initialization-clock-fixture-nov01.cpp"
namespace {
struct StageRngClockExperiment {
 u32 callback=0,index=0,point=0,delivered=0,failed=0,object=~0u,primitive=~0u,owner_stage=0;
 u64 ready=0,before=0;
} stage_rng_experiment;
}
API(stage_rng_clock_install) u32 stage_rng_clock_install(u32 callback,u32 index,u32 point,u64 ready){
 auto& e=stage_rng_experiment;
 if(e.callback||!callback||point>1||public_player_observations!=1||!session.battle||session.stage_load_object_boundary||ready<probe_clock_ns)return 0;
 e.callback=callback;e.index=index;e.point=point;e.ready=ready;
 session.stage_load_object_boundary=[](const Stage& owner,const AnmVm&,u32 object,u32 primitive,u32 index,AnmManager::VmBoundaryTh14 point){
  auto& e=stage_rng_experiment;
  if(!e.delivered&&session.state.stage==3&&public_player_observations==e.callback&&index==e.index&&u32(point)==e.point){
   e.before=probe_clock_ns;e.object=object;e.primitive=primitive;e.owner_stage=owner.state.stage_number;
   if(probe_clock_ns>e.ready){e.failed=1;return false;}
   probe_clock_ns=e.ready;++e.delivered;
  }
  return true;
 };
 return 1;
}
API(stage_rng_clock_word) u32 stage_rng_clock_word(u32 field){
 const auto& e=stage_rng_experiment;
 const u32 words[]={e.callback,e.index,e.point,e.delivered,e.failed,e.object,e.primitive,e.owner_stage,u32(e.before),u32(e.before>>32),u32(e.ready),u32(e.ready>>32)};
 return field<12?words[field]:~0u;
}
