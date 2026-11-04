// Replay a measured worker window between two world-camera perspective calls.
// No original camera, RNG, or gameplay values enter the implementation.
#include "th14-full-camera-observer-fixture-nov04.cpp"
namespace {
u32 perspective_window_callback=0,perspective_window_ordinal=0;
u32 perspective_window_visits=0,perspective_window_delivered=0;
u64 perspective_window_ready=0;
bool perspective_window_failed=false;
}
API(observed_perspective_window) u32 observed_perspective_window(u32 callback,u32 ordinal,u64 ready){
 if(perspective_window_callback||!callback||!ordinal||ready<probe_clock_ns)return 0;
 perspective_window_callback=callback;perspective_window_ordinal=ordinal;perspective_window_ready=ready;
 static auto previous=session.stage_load_perspective_boundary;
 session.stage_load_perspective_boundary=[](const SceneCamera& camera,u32 point){
  if(point==5&&public_player_observations==perspective_window_callback){
   ++perspective_window_visits;
   if(perspective_window_visits==perspective_window_ordinal){
    if(probe_clock_ns>perspective_window_ready)perspective_window_failed=true;
    else {probe_clock_ns=perspective_window_ready;++perspective_window_delivered;}
   }
  }
  return !perspective_window_failed&&(!previous||previous(camera,point));
 };
 return 1;
}
API(observed_perspective_window_state) u32 observed_perspective_window_state(u32 field){
 return field==0?perspective_window_delivered:field==1?perspective_window_failed:perspective_window_visits;
}
