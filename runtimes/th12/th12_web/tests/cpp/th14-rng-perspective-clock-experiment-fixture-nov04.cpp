// Controlled experiments; no original camera or RNG values enter the engine.
#include "th14-stage-rng-clock-experiment-fixture-nov04.cpp"
namespace {u32 perspective_clock_callback=0,perspective_clock_point=0,perspective_clock_delivered=0,perspective_clock_failed=0;u64 perspective_clock_ready=0,perspective_clock_before=0;}
API(perspective_clock_install) u32 perspective_clock_install(u32 callback,u32 point,u64 ready){
 if(perspective_clock_callback||!callback||point>5||public_player_observations!=1||!session.battle||session.stage_load_perspective_boundary||ready<probe_clock_ns)return 0;
 perspective_clock_callback=callback;perspective_clock_point=point;perspective_clock_ready=ready;
 session.stage_load_perspective_boundary=[](const SceneCamera&,u32 point){
  if(!perspective_clock_delivered&&session.state.stage==2&&public_player_observations==perspective_clock_callback&&point==perspective_clock_point){
   perspective_clock_before=probe_clock_ns;
   if(probe_clock_ns>perspective_clock_ready){perspective_clock_failed=1;return false;}
   probe_clock_ns=perspective_clock_ready;++perspective_clock_delivered;
  }
  return true;
 };
 return 1;
}
API(perspective_clock_word) u32 perspective_clock_word(u32 field){
 const u32 words[]={perspective_clock_callback,perspective_clock_point,perspective_clock_delivered,perspective_clock_failed,u32(perspective_clock_before),u32(perspective_clock_before>>32),u32(perspective_clock_ready),u32(perspective_clock_ready>>32)};
 return field<8?words[field]:~0u;
}
