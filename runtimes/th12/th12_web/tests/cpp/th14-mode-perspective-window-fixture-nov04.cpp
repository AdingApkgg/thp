// Diagnostic windows derived from legacy event ordinals. These older captures
// lack the full source-read witness; their exact instruction schedule is unknown.
#include "th14-full-camera-observer-fixture-nov04.cpp"
namespace {
struct ModePerspectiveWindow {u32 callback=0,ordinal=0,visits=0,delivered=0;u64 ready=0;bool failed=false;};
ModePerspectiveWindow mode_windows[8];bool mode_windows_installed=false;
}
API(diagnostic_mode_window) u32 diagnostic_mode_window(u32 stage,u32 callback,u32 ordinal,u64 ready){
 if(stage<2||stage>6||!callback||!ordinal||public_player_observations!=1||mode_windows[stage].callback||ready<probe_clock_ns)return 0;
 mode_windows[stage].callback=callback;mode_windows[stage].ordinal=ordinal;mode_windows[stage].ready=ready;
 if(!mode_windows_installed){
  mode_windows_installed=true;static auto previous=session.stage_load_perspective_boundary;
  session.stage_load_perspective_boundary=[](const SceneCamera& camera,u32 point){
   if(point==5)for(u32 stage=2;stage<=6;++stage){auto& window=mode_windows[stage];
    if(!window.callback||public_player_observations!=window.callback)continue;
    if(++window.visits==window.ordinal){
     if(!session.battle||session.battle->pending_stage!=stage||probe_clock_ns>window.ready)window.failed=true;
     else {probe_clock_ns=window.ready;++window.delivered;}
    }
    if(window.failed)return false;
   }
   return !previous||previous(camera,point);
  };
 }
 return 1;
}
API(diagnostic_mode_window_state) u32 diagnostic_mode_window_state(u32 stage,u32 field){
 if(stage>=8)return ~0u;const auto& w=mode_windows[stage];return field==0?w.delivered:field==1?w.failed:w.visits;
}
