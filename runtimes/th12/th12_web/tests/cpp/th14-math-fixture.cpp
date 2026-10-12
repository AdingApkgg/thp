#include "../../cpp/game/AnmVm.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmVm vm;
static AnmEnvironment env;
alignas(4) static u8 code[128];
API(run) i32 run(u32 op,u32 refs,u32 count,u32 a,u32 b,u32 c,u32 d,i32 x,i32 y,u32 seed,u32 visual){
    vm={};vm.initialize();env.rate=1;vm.timer.set(0,&env.rate);vm.flags|=visual?0x40000000:0;
    env.script_rng={u16(seed),0,0};env.visual_rng={54321,0,0};
    const i32 ints[]={x,y,2,9};const float floats[]={x/8.f,y/8.f,.5f,.75f};
    std::memcpy(vm.integers,ints,sizeof(ints));std::memcpy(vm.floats,floats,sizeof(floats));
    std::memset(code,0,sizeof(code));auto* command=reinterpret_cast<AnmInstruction*>(code);
    command->opcode=anm_canonical_opcode(op);command->length=8+count*4;command->references=refs;
    const u32 args[]={a,b,c,d};std::memcpy(code+8,args,count*4);
    for(u32 off:{u32(command->length),64u}){auto* next=reinterpret_cast<AnmInstruction*>(code+off);next->length=8;next->time=30000;}
    vm.script_begin=vm.instruction=command;
    return vm.update(env);
}
API(word) u32 word(u32 i){
    if(i<4)return u32(vm.integers[i]);
    if(i<8){u32 v;std::memcpy(&v,code+8+(i-4)*4,4);return v;}
    if(i==8)return reinterpret_cast<u8*>(vm.instruction)-code;
    if(i==9)return env.script_rng.seed;
    if(i==10)return env.script_rng.calls;
    return env.visual_rng.calls;
}
API(real) float real(u32 i){return i<4?vm.floats[i]:vm.timer.fractional;}
