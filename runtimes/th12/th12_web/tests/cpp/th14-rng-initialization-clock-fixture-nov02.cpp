#include "th14-initialization-clock-fixture-nov01.cpp"
namespace {u32 rng_callback=0,rng_effect=0,rng_point=0,rng_delivered=0,rng_failed=0,rng_visits=0;u64 rng_ready=0;}
API(observed_rng_initialization_clock) u32 observed_rng_initialization_clock(u32 callback,u32 effect,u32 point,u64 ready){
 if(rng_callback||!callback||!session.battle||point>4||ready<probe_clock_ns)return 0;
 rng_callback=callback;rng_effect=effect;rng_point=point;rng_ready=ready;
 session.animations.before_rng_boundary=[](const AnmVm& vm,Rng& random,RngBoundary point){
  if(public_player_observations==rng_callback&&&random==&session.animations.script_rng&&vm.th13_effect==rng_effect&&u32(point)==rng_point){
   ++rng_visits;
   if(!rng_delivered){if(probe_clock_ns>rng_ready)rng_failed=1;else probe_clock_ns=rng_ready;++rng_delivered;}
  }
  return true;
 };
 return 1;
}
API(observed_rng_initialization_clock_state) u32 observed_rng_initialization_clock_state(u32 field){switch(field){case 0:return rng_delivered;case 1:return rng_failed;case 2:return rng_visits;default:return ~0u;}}
