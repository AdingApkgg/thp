#include "../../cpp/game/AnmVm.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmVm vm;static AnmEnvironment env;static AnmInstruction commands[]={{0,8,30000,0},{-1,8,0,0}};
API(run) i32 run(u32 rate,u32 sample,u32 mask,u32 enabled){
 constexpr float rates[]={0,.125,.5,1,1.5,2,-.25},positions[]={0.f,-0.f,3.1415927410125732f,-3.1415927410125732f,128,-256,1024,-.375},speeds[]={0.f,-0.f,.125,-.25,3.25,-17.75,1024,-1024};
 vm.initialize();vm.flags=3;vm.flags2=enabled<<24;vm.script_begin=vm.instruction=commands;env.rate=rates[rate];
 float* values[]={&vm.rotation.x,&vm.rotation.y,&vm.rotation.z,&vm.scale.x,&vm.scale.y,&vm.uv_offset.x,&vm.uv_offset.y};
 float* velocities[]={&vm.angular_velocity.x,&vm.angular_velocity.y,&vm.angular_velocity.z,&vm.scale_velocity.x,&vm.scale_velocity.y,&vm.scroll_velocity.x,&vm.scroll_velocity.y};
 for(u32 i=0;i<7;++i){*values[i]=positions[(sample+i)%8];*velocities[i]=mask&(1<<i)?speeds[(sample+i)%8]:0;}
 return vm.update(env);
}
API(word) u32 word(u32 field){if(field==7)return vm.flags;const float values[]={vm.rotation.x,vm.rotation.y,vm.rotation.z,vm.scale.x,vm.scale.y,vm.uv_offset.x,vm.uv_offset.y};u32 value;std::memcpy(&value,&values[field],4);return value;}
