#include "SceneCameraReadJobTh14.hpp"
#include "SceneCompositor.hpp"
#include <cstddef>
#include <cstring>
#include <new>
using namespace th11;
namespace {
u32 input[75]{},output[75]{},layout_words[8]{},phases[8*4]{},phase_count=0;
alignas(8) unsigned char storage[sizeof(SceneCamera)+8];
}
#define API(name) extern "C" __attribute__((export_name(#name)))
API(input_data) u32* input_data(){return input;}
API(output_data) u32* output_data(){return output;}
API(phase_data) u32* phase_data(){return phases;}
API(phase_size) u32 phase_size(){return phase_count;}
API(compute) void compute(u32 perspective,u32 alignment_offset){
 if(alignment_offset!=0&&alignment_offset!=4)std::abort();
 auto& camera=*new(storage+alignment_offset)SceneCamera{};phase_count=0;
 for(u32 i=0;i<75;++i)std::memcpy(reinterpret_cast<u8*>(&camera)+SceneCameraReadJobTh14::source_offset(i),input+i,4);
 SceneCameraPerspectiveScopeTh14 scope(camera,nullptr,[](void*,const SceneCamera& value,u32 point){
  if(phase_count>=8)std::abort();auto* row=phases+phase_count++*4;row[0]=point;std::memcpy(row+1,&value.right,12);return true;
 });
 if(perspective)camera.perspective();else camera.screen();
 for(u32 i=0;i<75;++i)std::memcpy(output+i,reinterpret_cast<const u8*>(&camera)+SceneCameraReadJobTh14::source_offset(i),4);
 camera.~SceneCamera();
}
API(layout_data) u32* layout_data(){
 AnmManager manager;SceneCompositor compositor(manager);
 layout_words[0]=sizeof(SceneCamera);layout_words[1]=alignof(SceneCamera);layout_words[2]=sizeof(SceneCompositor);layout_words[3]=alignof(SceneCompositor);
 layout_words[4]=u32(reinterpret_cast<const u8*>(&compositor.world_camera)-reinterpret_cast<const u8*>(&compositor));
 layout_words[5]=u32(reinterpret_cast<std::uintptr_t>(&compositor.world_camera)&7u);
 layout_words[6]=u32(reinterpret_cast<std::uintptr_t>(&compositor.world_camera.right)&7u);
 layout_words[7]=offsetof(SceneCamera,right);return layout_words;
}
