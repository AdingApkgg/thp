#include "../../cpp/game/AnmVm.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmVm vms[4];static u32 captured;
struct Environment:AnmEnvironment {i32 status=0;int th16_pre_update(AnmVm&)override{std::memcpy(&captured,&rate,4);return status;}};
static Environment env;
API(run) i32 run(u32 ri,u32 si,u32 length,u32 independent,u32 force,i32 status){
 constexpr float rates[]={0.f,-0.f,.125,.5,1,1.5,2,-.25},slowdowns[]={0.f,-0.f,.125,.5,1,1.5,-.5};
 for(u32 i=0;i<4;++i){auto& vm=vms[i];vm.initialize();vm.flags2=((independent>>i)&1)<<16;vm.th16_transform_parent=i+1<length?&vms[i+1]:nullptr;vm.slowdown_factor=i+1==length?slowdowns[si]:.25f*(i+1);}
 vms[0].flags2|=force<<9;vms[0].th16_callbacks[0]=1;env.rate=rates[ri];env.status=status;return vms[0].update(env);
}
API(value) u32 value(u32 field){if(!field)return captured;u32 v;std::memcpy(&v,&env.rate,4);return v;}
