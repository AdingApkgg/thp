#include "../../cpp/game/AnmManager.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include "../../cpp/game/AnmGeometry.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager env;static AnmVm vm;
struct Script{AnmInstruction command;i32 effect;AnmInstruction idle;};
static Script script;
static AnmTh14Ribbon& ribbon(){return *static_cast<AnmTh14Ribbon*>(vm.geometry);}
API(begin) i32 begin(u32 seed,float rate,u32 independent){
    env.release_geometry(vm);vm={};vm.initialize();env.rate=rate;env.script_rng={u16(seed),0,0};
    vm.flags2=0x800000|(independent<<8);vm.native_prefix_position={17.25,-9.5,.125};
    script={{i16(anm_canonical_opcode(508)),12,0,0},8,{0,8,30000,0}};
    vm.instruction=vm.script_begin=&script.command;vm.timer.set(0,&env.rate);return vm.update(env);
}
API(tick) i32 tick(u32 frame){if(frame==24)vm.instruction=nullptr;if(frame==36)ribbon().angle=.125;return vm.update(env);}
API(initial) float initial(u32 i){return i==0?ribbon().phase:i==1?vm.position.x:i==2?vm.position.y:i==3?vm.position.z:float(vm.layer);}
API(state) float state(u32 i){return i==0?ribbon().angular_speed:i==1?ribbon().angle:i==2?ribbon().timer.fractional:env.rate;}
API(word) u32 word(u32 i){return i==0?env.script_rng.seed:i==1?env.script_rng.calls:i==2?u32(ribbon().timer.current):u32(ribbon().timer.previous);}
API(step) float step(u32 i){const auto p=ribbon().steps[i/3];return i%3==0?p.x:i%3==1?p.y:p.z;}
API(vertex) float vertex(u32 i,u32 field){const auto& v=ribbon().vertices[i];return field==0?v.position.x:field==1?v.position.y:field==2?v.position.z:field==4?v.uv.x:v.uv.y;}
API(color) u32 color(u32 i){return ribbon().vertices[i].color;}
