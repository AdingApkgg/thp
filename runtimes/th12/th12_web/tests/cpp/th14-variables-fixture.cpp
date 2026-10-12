#include "../../cpp/game/AnmVm.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmVm vm,parent;
static AnmEnvironment env;
static double result;
API(run) void run(u32 kind,float value,i32 bound,u32 p){
    vm={};parent={};vm.initialize();parent.initialize();
    env.script_rng={12345,0,0};env.visual_rng={54321,0,0};
    const i32 ints[]={-11,24,-31,55};const float floats[]={.5f,-2.25f,3.75f,9.125f};
    std::memcpy(vm.integers,ints,sizeof(ints));std::memcpy(vm.floats,floats,sizeof(floats));
    vm.extra_floats={5.5f,-6.25f,7.75f};vm.extra_integers[0]=17;vm.extra_integers[1]=-19;
    vm.random_scale={1.25f,-3.5f};vm.random_bound=bound;
    vm.script_position={3,5,8};vm.rotation={.25f,.5f,.375f};
    vm.parent=p?&parent:nullptr;parent.rotation.z=p==1?-.625f:7.125f;
    env.reference_positions[0]={16.5f,23.75f,33};env.reference_positions[1]={-7,13,42};
    if(kind==0)result=u32(vm.integer_value(i32(value),env));
    else if(kind==1)result=vm.float_value(value,env);
    else {
        i32 integer=i32(value);float real=value;
        const void* pointer=kind==2?static_cast<void*>(vm.integer_destination(&integer)):static_cast<void*>(vm.float_destination(&real));
        const void* fields[]={vm.integers,vm.integers+1,vm.integers+2,vm.integers+3,vm.floats,vm.floats+1,vm.floats+2,vm.floats+3,
            &vm.extra_floats.x,&vm.extra_floats.y,&vm.extra_floats.z,vm.extra_integers,vm.extra_integers+1,
            &vm.random_scale.x,&vm.random_scale.y,&vm.random_bound,
            &vm.script_position.x,&vm.script_position.y,&vm.script_position.z,&vm.rotation.x,&vm.rotation.y,&vm.rotation.z};
        result=-1;for(u32 i=0;i<22;++i)if(pointer==fields[i])result=i;
    }
}
API(value) double value(){return result;}
API(rng_case) float rng_case(u32 seed,u32 signed_value){vm.random_scale={1,1};env.script_rng={u16(seed),0,0};return float(vm.float_value(signed_value?10012.f:10011.f,env));}
API(rng) u32 rng(u32 i){switch(i){case 0:return env.script_rng.seed;case 1:return env.script_rng.calls;case 2:return env.visual_rng.seed;default:return env.visual_rng.calls;}}
