// A relative ordering host: no original seed, call count or VM identity is input.
#include "th14-render-dimensions-observer-fixture-nov04.cpp"
namespace {
struct FirstReadOrder {u32 stage=0,callback=0,delivered=0,failed=0,file=0,script=0,script_calls=0,visual_calls=0,point=0;u64 pump=0,ready=0,before=0;} first_read_order;
}
API(observed_rng_first_read_order) u32 observed_rng_first_read_order(u32 stage,u32 callback,u64 pump,u64 ready,u32 point){
 auto& e=first_read_order;if(point>1||e.callback||!callback||stage<2||stage>6||pump>ready||ready<probe_clock_ns||public_player_observations!=1)return 0;
 e.stage=stage;e.callback=callback;e.pump=pump;e.ready=ready;e.point=point;
 static auto previous=session.animations.before_rng_boundary;
 session.animations.before_rng_boundary=[](const AnmVm& vm,Rng& rng,RngBoundary point){
  auto& e=first_read_order;
  if(!e.delivered&&session.state.stage==e.stage&&public_player_observations==e.callback&&probe_clock_ns>=e.pump&&&rng==&session.animations.script_rng&&u32(point)==e.point){
   e.before=probe_clock_ns;e.file=vm.file_index;e.script=vm.script_index;e.script_calls=rng.calls;e.visual_calls=session.animations.visual_rng.calls;
   if(probe_clock_ns>e.ready){e.failed=1;return false;}
   probe_clock_ns=e.ready;++e.delivered;
  }
  return !previous||previous(vm,rng,point);
 };
 return 1;
}
API(observed_rng_first_read_word) u32 observed_rng_first_read_word(u32 index){
 const auto& e=first_read_order;const u32 words[]={e.stage,e.callback,e.delivered,e.failed,e.file,e.script,e.script_calls,e.visual_calls,u32(e.before),u32(e.before>>32),u32(e.ready),u32(e.ready>>32)};
 return index<12?words[index]:~0u;
}

namespace {u32 relative_camera_stage=0,relative_camera_callback=0,relative_camera_ordinal=0,relative_camera_visits=0,relative_camera_delivered=0,relative_camera_failed=0,relative_camera_point=5;u64 relative_camera_ready=0;}
API(observed_relative_camera_read_order) u32 observed_relative_camera_read_order(u32 stage,u32 callback,u32 ordinal,u32 point,u64 ready){
 if(relative_camera_callback||!callback||!ordinal||point>5||ready<probe_clock_ns||public_player_observations!=1)return 0;
 relative_camera_stage=stage;relative_camera_callback=callback;relative_camera_ordinal=ordinal;relative_camera_point=point;relative_camera_ready=ready;
 static auto previous=session.stage_load_perspective_boundary;
 session.stage_load_perspective_boundary=[](const SceneCamera& camera,u32 point){
  if(session.state.stage==relative_camera_stage&&public_player_observations==relative_camera_callback&&point==relative_camera_point){
   if(++relative_camera_visits==relative_camera_ordinal){
    if(probe_clock_ns>relative_camera_ready){relative_camera_failed=1;return false;}
    probe_clock_ns=relative_camera_ready;++relative_camera_delivered;
   }
  }
  return !previous||previous(camera,point);
 };
 return 1;
}
API(observed_relative_camera_word) u32 observed_relative_camera_word(u32 index){
 const u32 values[]={relative_camera_stage,relative_camera_callback,relative_camera_ordinal,relative_camera_point,relative_camera_visits,relative_camera_delivered,relative_camera_failed};
 return index<7?values[index]:~0u;
}
