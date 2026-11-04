// Isolated camera input/output observations, without a GameSession or clocks.
#include "SceneCamera.hpp"
#include <cstring>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
namespace {
SceneCamera camera;u32 snapshots[8][75]{},phase_order[8]{},phase_count=0,phase_mask=0;
u32 offset(u32 index){return index<18?index*4:index<21?offsetof(SceneCamera,target_offset)+(index-18)*4:index==21?offsetof(SceneCamera,fov):index==22?offsetof(SceneCamera,render_width):index==23?offsetof(SceneCamera,render_height):offsetof(SceneCamera,view)+(index-24)*4;}
}
API(normalize_input_word) u32 normalize_input_word(u32 index,u32 word){if(index>=75)return 0;std::memcpy(reinterpret_cast<u8*>(&camera)+offset(index),&word,4);return 1;}
API(normalize_run) u32 normalize_run(){
 phase_count=phase_mask=0;std::memset(snapshots,0,sizeof snapshots);
 SceneCameraPerspectiveScopeTh14 scope(camera,nullptr,[](void*,const SceneCamera& value,u32 point){
  if(point>=8||phase_count>=8)return false;phase_order[phase_count++]=point;phase_mask|=1u<<point;
  for(u32 i=0;i<75;++i)std::memcpy(&snapshots[point][i],reinterpret_cast<const u8*>(&value)+offset(i),4);
  return true;
 });
 camera.perspective();return phase_mask;
}
API(normalize_phase_word) u32 normalize_phase_word(u32 point,u32 index){return point<8&&index<75?snapshots[point][index]:~0u;}
API(normalize_phase_order) u32 normalize_phase_order(u32 index){return index<phase_count?phase_order[index]:~0u;}
API(normalize_phase_count) u32 normalize_phase_count(){return phase_count;}
