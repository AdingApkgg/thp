#include "../../cpp/game/AnmVm.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmVm vm;
struct Env:AnmEnvironment{bool update_geometry(AnmVm&)override{return true;}};
static Env env;
static u32 float_bits(float f){u32 v;std::memcpy(&v,&f,4);return v;}
alignas(4) static u8 code[40];
API(run) int run(u32 seed,u32 visual,u32 refs,u32 flags2,u32 a,u32 b){
 vm={};vm.initialize();env.rate=1;env.script_rng={u16(seed),0,0};env.visual_rng={u16(visual),0,0};vm.flags2=flags2;vm.timer.set(0,&env.rate);
 std::memset(code,0,sizeof code);auto* p=reinterpret_cast<AnmInstruction*>(code);p->opcode=anm_canonical_opcode(416);p->length=16;p->references=u16(refs);std::memcpy(code+8,&a,4);std::memcpy(code+12,&b,4);
 auto* next=reinterpret_cast<AnmInstruction*>(code+16);next->length=8;next->time=32760;auto* end=reinterpret_cast<AnmInstruction*>(code+24);end->opcode=-1;end->length=8;end->time=32767;vm.script_begin=vm.instruction=p;return vm.update(env);
}
API(word) u32 word(u32 i){const u32 values[]={vm.flags2,float_bits(vm.scale_velocity.x),float_bits(vm.scale_velocity.y),env.script_rng.seed,env.script_rng.calls,env.visual_rng.seed,env.visual_rng.calls};return values[i];}
