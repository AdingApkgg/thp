// Replay only observed read-order windows, retaining the model's own source camera.
#include "th14-75-camera-replay-cursor-fixture-nov04.cpp"
namespace {
struct SourceReadWindow {u32 callback=0,ordinal=0,point=0,visits=0,delivered=0,failed=0;u64 ready=0;SceneCamera source;};
SourceReadWindow source_read_windows[8];bool source_read_windows_installed=false;
}
API(observed_source_read_window) u32 observed_source_read_window(u32 stage,u32 callback,u32 ordinal,u32 point,u64 ready){
 if(stage<2||stage>6||!callback||!ordinal||point>5||public_player_observations!=1||source_read_windows[stage].callback||ready<probe_clock_ns)return 0;
 auto& window=source_read_windows[stage];window.callback=callback;window.ordinal=ordinal;window.point=point;window.ready=ready;
 if(!source_read_windows_installed){
  source_read_windows_installed=true;static auto previous=session.stage_load_perspective_boundary;
  session.stage_load_perspective_boundary=[](const SceneCamera& camera,u32 point){
   for(u32 stage=2;stage<=6;++stage){auto& w=source_read_windows[stage];
    if(!w.callback||public_player_observations!=w.callback||point!=w.point)continue;
    if(++w.visits==w.ordinal){
     if(!session.battle||session.battle->pending_stage!=stage||probe_clock_ns>w.ready)w.failed=1;
     else {w.source=camera;probe_clock_ns=w.ready;++w.delivered;}
    }
    if(w.failed)return false;
   }
   return !previous||previous(camera,point);
  };
 }
 return 1;
}
API(source_read_window_state) u32 source_read_window_state(u32 stage,u32 index){
 if(stage>=8)return ~0u;const auto& w=source_read_windows[stage];const u32 words[]={w.callback,w.ordinal,w.point,w.visits,w.delivered,w.failed};return index<6?words[index]:~0u;
}
API(source_read_camera_word) u32 source_read_camera_word(u32 stage,u32 index){
 if(stage>=8||index>=75||!source_read_windows[stage].delivered)return ~0u;
 const auto& camera=source_read_windows[stage].source;
 if(index==22)return camera.render_width;if(index==23)return camera.render_height;
 const u32 offset=index<18?index*4:index<21?offsetof(SceneCamera,target_offset)+(index-18)*4:index==21?offsetof(SceneCamera,fov):offsetof(SceneCamera,view)+(index-24)*4;
 u32 value;std::memcpy(&value,reinterpret_cast<const u8*>(&camera)+offset,4);return value;
}
