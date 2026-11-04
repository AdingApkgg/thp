// Independent per-stage relative RNG-read windows, with no RNG value input.
#include "th14-source-read-camera-cursor-fixture-nov04.cpp"
namespace {
struct ScriptReadWindow {u32 callback=0,point=0,delivered=0,failed=0,file=0,script=0,calls=0,visual_calls=0;u64 pump=0,ready=0,before=0;};
ScriptReadWindow script_read_windows[8];bool script_read_windows_installed=false;
}
API(observed_first_script_read_window) u32 observed_first_script_read_window(u32 stage,u32 callback,u64 pump,u64 ready,u32 point){
 if(stage<2||stage>6||!callback||point>1||pump>ready||ready<probe_clock_ns||public_player_observations!=1||script_read_windows[stage].callback)return 0;
 auto& w=script_read_windows[stage];w.callback=callback;w.pump=pump;w.ready=ready;w.point=point;
 if(!script_read_windows_installed){
  script_read_windows_installed=true;static auto previous=session.animations.before_rng_boundary;
  session.animations.before_rng_boundary=[](const AnmVm& vm,Rng& rng,RngBoundary point){
   const u32 stage=session.state.stage;
   if(stage>=2&&stage<=6){auto& w=script_read_windows[stage];
    if(w.callback&&!w.delivered&&public_player_observations==w.callback&&probe_clock_ns>=w.pump&&&rng==&session.animations.script_rng&&u32(point)==w.point){
     w.before=probe_clock_ns;w.file=vm.file_index;w.script=vm.script_index;w.calls=rng.calls;w.visual_calls=session.animations.visual_rng.calls;
     if(probe_clock_ns>w.ready)w.failed=1;else{probe_clock_ns=w.ready;++w.delivered;}
    }
    if(w.failed)return false;
   }
   return !previous||previous(vm,rng,point);
  };
 }
 return 1;
}
API(first_script_read_window_word) u32 first_script_read_window_word(u32 stage,u32 index){
 if(stage>=8)return ~0u;const auto& w=script_read_windows[stage];
 const u32 words[]={w.callback,w.point,w.delivered,w.failed,w.file,w.script,w.calls,w.visual_calls,u32(w.before),u32(w.before>>32),u32(w.ready),u32(w.ready>>32)};return index<12?words[index]:~0u;
}
