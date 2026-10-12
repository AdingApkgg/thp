#include "../../cpp/game/AnmVm.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmVm vm;
static AnmEnvironment env;
alignas(4) static u8 code[128];
API(begin_case) void begin_case(u32 wait,float rate,u32 fallback){
    vm={};vm.initialize();env.rate=rate;vm.timer.set(0,&env.rate);vm.color=0xab123456;
    std::memset(code,0,sizeof(code));u32 cursor=0;
    auto append=[&](i16 op,i16 time,u32 count,i32 arg=0){
        auto* cmd=reinterpret_cast<AnmInstruction*>(code+cursor);cmd->opcode=op==-1?-1:i16(anm_canonical_opcode(op));
        cmd->length=8+4*count;cmd->time=time;if(count)std::memcpy(code+cursor+8,&arg,4);cursor+=cmd->length;
    };
    append(403,0,1,37);append(wait,0,0);append(5,10,1,7);append(403,10,1,201);append(7,12,0);
    if(fallback){append(5,20,1,-1);append(403,20,1,77);append(2,21,0);}
    append(-1,32767,0);vm.script_begin=vm.instruction=reinterpret_cast<AnmInstruction*>(code);
}
API(tick) i32 tick(i32 pending){if(pending)vm.pending_interrupt=i16(pending);return vm.update(env);}
API(word) i32 word(u32 i){
    if(i==0)return vm.instruction?reinterpret_cast<u8*>(vm.instruction)-code:-1;
    if(i==1)return (vm.flags&1)!=0;
    if(i==2)return (vm.flags&0x1000)!=0;
    if(i==3)return vm.color;
    return vm.saved_instruction?reinterpret_cast<u8*>(vm.saved_instruction)-code:-1;
}
API(real) float real(u32 i){return i?vm.saved_timer.fractional:vm.timer.fractional;}
