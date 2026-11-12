#include "StageCppDecodeTh14.hpp"
#include "StageCppWorkerTh14.hpp"
#include <atomic>
#include <cstring>
using namespace th11;
namespace {
u32 input[75]{},output[150]{},meta[8]{};
std::atomic<int> gate{0};
void signal(int n){gate.store(n,std::memory_order_release);__builtin_wasm_memory_atomic_notify(reinterpret_cast<int*>(&gate),1);}
bool wait(int n){for(u32 tries=0;tries<100;++tries){int v=gate.load(std::memory_order_acquire);if(v==n)return true;if(v<0)return false;__builtin_wasm_memory_atomic_wait32(reinterpret_cast<int*>(&gate),v,50000000);}return false;}
void encode(u32* out,const SceneCamera& camera){for(u32 i=0;i<75;++i)std::memcpy(out+i,reinterpret_cast<const u8*>(&camera)+SceneCameraReadJobTh14::source_offset(i),4);}
}
#define API(name) extern "C" __attribute__((export_name(#name)))
API(input_data) u32* input_data(){return input;}
API(output_data) const u32* output_data(){return output;}
API(run_case) const u32* run_case(u32 mode,u32 after_math,u32 stage_number){
 std::memset(meta,0,sizeof(meta));gate.store(0,std::memory_order_release);
 SceneCamera world{};
 for(u32 i=0;i<75;++i)std::memcpy(reinterpret_cast<u8*>(&world)+SceneCameraReadJobTh14::source_offset(i),input+i,4);
 AnmManager manager;AnmResource background,text;u32 color=0;
 StageResource resource;resource.instructions.emplace_back();
 StageCppDecodeTh14 decode;StageCppWorkerTh14 worker;
 const bool started=worker.start([&](){
  if(!decode.begin_hud_before_initialized(0))return false;
  decode.initialized();
  return decode.run([&](u32 phase,u32){
   if(phase!=1)return true;
   if(!wait(1))return false;
   bool ok=decode.create_scene_owner(manager,background,text,color,stage_number,world)
    &&decode.prepare_scene_storage(0)&&decode.capture_scene_camera(world)
    &&decode.initialize_scene_owner(resource,stage_number);
   signal(ok?2:-1);return ok;
  });
 });
 if(!started){meta[0]=1;return meta;}
 if(!after_math){signal(1);if(!wait(2)){meta[0]=2;decode.cancel();}}
 if(mode)world.perspective();else world.screen();
 if(after_math){signal(1);if(!wait(2)){meta[0]=3;decode.cancel();}}
 worker.join();
 meta[1]=worker.poll()==ReplayRngRestoreResultTh14::Ready;
 auto owner=decode.take_scene_owner();meta[2]=bool(owner);
 if(owner){encode(output,owner->state.camera);meta[3]=owner->state.stage_number;meta[4]=u32(owner->resource.instructions.size());}
 encode(output+75,world);meta[5]=mode;meta[6]=after_math;meta[7]=75;
 return meta;
}
