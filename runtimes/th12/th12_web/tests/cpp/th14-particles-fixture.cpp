#include "../../cpp/game/AnmManager.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include "../../cpp/game/AnmGeometry.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager env;static AnmVm vm;static AnmResource resource;static u32 base_id;
static AnmTh14Particles& effect(){return *static_cast<AnmTh14Particles*>(vm.geometry);}
struct Script{AnmInstruction command;i32 argument;AnmInstruction idle,end;};
static Script script;
API(begin) i32 begin(u32 seed,float rate,float slowdown){
    env.clear();env.release_geometry(vm);vm={};vm.initialize();resource={};resource.scripts.resize(153);
    const Script child{{72,12,0,0},1,{0,8,30000,0},{-1,8,32767,0}};
    for(const auto i:{151,152}){auto& bytes=resource.scripts[i].bytes;bytes.resize(sizeof child);std::memcpy(bytes.data(),&child,sizeof child);}
    env.rate=rate;env.script_rng={54321,0,0};env.visual_rng={u16(seed),0,0};base_id=0;
    vm.flags2=0x800000;vm.position={17.25,-9.5,.125};vm.rotation={.125,-.25,.35};vm.extra_floats.z=.75;
    vm.integers[0]=8;vm.color=0xab123456;vm.slowdown_factor=slowdown;vm.resource=&resource;
    script={{i16(anm_canonical_opcode(508)),12,0,0},7,{0,8,30000,0},{-1,8,32767,0}};
    vm.instruction=vm.script_begin=&script.command;vm.timer.set(0,&env.rate);return vm.update(env);
}
API(frame) i32 frame(u32 index){
    if(index==45)vm.interrupt(1);
    if(index==62)for(u32 i=3;i<=200;i+=3)if(auto* child=env.find(base_id+i))env.destroy(*child);
    if(index==71)env.clear();
    const int status=vm.update(env);
    if(index==0)base_id=effect().children[0]-1;
    if(index==70)anm_th14_particles_destroy(vm,env);
    return status;
}
API(finish_frame) i32 finish_frame(){for(u32 i=1;i<=200;++i)if(auto* child=env.find(base_id+i))if(child->update(env)!=0)return -1;return 0;}
API(exists) u32 exists(u32 id){return env.find(base_id+id)!=nullptr;}
API(word) u32 word(u32 id,u32 field){
    const auto* c=env.find(base_id+id);if(!c)return ~0u;
    switch(field){case 0:return c->script_index;case 1:return c->color;case 2:return c->integers[0];case 3:return c->age.current;case 4:return c->flags&1;case 5:return c->instruction==nullptr;default:return c->position_interpolation.duration;}
}
API(value) float value(u32 id,u32 field){
    const auto* c=env.find(base_id+id);if(!c)return 0;
    if(field==0)return c->slowdown_factor;if(field==1)return c->script_position.x;if(field==2)return c->script_position.y;if(field==3)return c->script_position.z;
    if(field==16)return c->position_interpolation.timer.fractional;
    const auto& v=c->position_interpolation;const float* values[]={v.start,v.end,v.initial_tangent,v.final_tangent};return values[(field-4)/3][(field-4)%3];
}
API(effect_word) u32 effect_word(u32 index){return index<200?(effect().children[index]?effect().children[index]-base_id:0):effect().states[index-200];}
API(effect_value) float effect_value(u32 index){
    if(index==0)return effect().timer.fractional;if(index==10)return env.rate;
    const auto& p=index<=3?effect().near_center:index<=6?effect().far_center:effect().origin;
    return (index-1)%3==0?p.x:(index-1)%3==1?p.y:p.z;
}
API(rng) u32 rng(u32 index){return index?env.visual_rng.calls:env.visual_rng.seed;}
