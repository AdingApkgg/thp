// Observe the complete source camera before the real Scene poll copies it.
#include "th14-render-dimensions-observed-window-fixture-nov04.cpp"
namespace {SceneCamera observed_source_camera;bool observed_source_captured=false;}
API(observed_dimensions_source_window) u32 observed_dimensions_source_window(u32 callback,u32 ordinal,u64 ready){
 if(!observed_perspective_window(callback,ordinal,ready))return 0;
 static auto previous=session.stage_load_perspective_boundary;
 session.stage_load_perspective_boundary=[](const SceneCamera& camera,u32 point){
  if(previous&&!previous(camera,point))return false;
  if(point==5&&perspective_window_delivered&&!observed_source_captured){observed_source_camera=camera;observed_source_captured=true;}
  return true;
 };
 return 1;
}
API(observed_source_camera_word) u32 observed_source_camera_word(u32 index){
 if(!observed_source_captured||index>=75)return ~0u;
 u32 offset=index<18?index*4:index<21?offsetof(SceneCamera,target_offset)+(index-18)*4:index==21?offsetof(SceneCamera,fov):index==22?offsetof(SceneCamera,render_width):index==23?offsetof(SceneCamera,render_height):offsetof(SceneCamera,view)+(index-24)*4;
 u32 value;std::memcpy(&value,reinterpret_cast<const u8*>(&observed_source_camera)+offset,4);return value;
}
API(observed_source_camera_captured) u32 observed_source_camera_captured(){return observed_source_captured;}
