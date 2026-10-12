#include "../../cpp/game/AnmVm.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmVm vm;static AnmEnvironment env;alignas(4) static u8 code[64];
API(run) i32 run(u32 op,i32 a,i32 b,u32 refs){
    vm={};vm.initialize();env.rate=1;vm.timer.set(0,&env.rate);
    const i32 ints[]={23,-11,0x40000001,-99};const float floats[]={1.5,-2.75,.125,448};std::memcpy(vm.integers,ints,sizeof ints);std::memcpy(vm.floats,floats,sizeof floats);
    std::memset(code,0,sizeof code);auto* p=reinterpret_cast<AnmInstruction*>(code);p->opcode=anm_canonical_opcode(op);p->references=refs;const bool real=op&1;const u32 count=op<112?2:3;p->length=8+count*4;
    const i32 args[]={refs&1?(real?10004:10000):-3,refs&2?(real?10005:10001):a,refs&4?(real?10006:10002):b};
    for(u32 i=0;i<count;++i){if(real){const float v=float(args[i]);std::memcpy(code+8+i*4,&v,4);}else std::memcpy(code+8+i*4,args+i,4);}
    // Future instruction leaves dispatch state intact and allows reading its offset.
    auto* next=reinterpret_cast<AnmInstruction*>(code+p->length);next->length=8;next->time=32760;vm.script_begin=vm.instruction=p;return vm.update(env);
}
API(word) u32 word(u32 n){u32 bits=0;if(n<4)return u32(vm.integers[n]);if(n<8)std::memcpy(&bits,vm.floats+n-4,4);else if(n<11)std::memcpy(&bits,code+8+(n-8)*4,4);return bits;}
API(advance) u32 advance(){return u32(reinterpret_cast<u8*>(vm.instruction)-code);}
API(run_branch) i32 run_branch(u32 op,u32 a_bits,u32 b_bits,u32 refs){
    vm={};vm.initialize();env.rate=1;vm.timer.previous=18;vm.timer.current=19;vm.timer.fractional=19.25;vm.timer.flags=1;vm.timer.rate=&env.rate;vm.integers[0]=23;vm.integers[1]=-11;vm.floats[0]=1.5;vm.floats[1]=-2.75;
    std::memset(code,0,sizeof code);auto* p=reinterpret_cast<AnmInstruction*>(code);p->opcode=anm_canonical_opcode(op);p->length=24;p->references=refs;
    const bool real=op&1;auto bits=[](float v){u32 result;std::memcpy(&result,&v,4);return result;};
    const u32 args[]={refs&1?(real?bits(10004.f):10000u):a_bits,refs&2?(real?bits(10005.f):10001u):b_bits,48,27};std::memcpy(code+8,args,sizeof args);
    for(u32 off:{24u,48u}){auto* stop=reinterpret_cast<AnmInstruction*>(code+off);stop->opcode=2;stop->length=8;stop->time=-32768;}
    vm.script_begin=vm.instruction=p;return vm.update(env);
}
API(branch_word) u32 branch_word(u32 n){switch(n){case 0:return vm.trace[1].offset;case 1:return u32(vm.timer.previous);case 2:return u32(vm.timer.current);default:{u32 bits;std::memcpy(&bits,&vm.timer.fractional,4);return bits;}}}

API(run_trig) i32 run_trig(u32 op,u32 a_bits,u32 refs){
    vm={};vm.initialize();env.rate=1;vm.timer.set(0,&env.rate);float a;std::memcpy(&a,&a_bits,4);
    const float floats[]={1.5,a,.125,448};std::memcpy(vm.floats,floats,sizeof floats);
    std::memset(code,0,sizeof code);auto* p=reinterpret_cast<AnmInstruction*>(code);p->opcode=anm_canonical_opcode(op);p->references=refs;p->length=16;
    const float args[]={refs&1?10004.f:-3.f,refs&2?10005.f:a};std::memcpy(code+8,args,sizeof args);
    auto* stop=reinterpret_cast<AnmInstruction*>(code+16);stop->opcode=2;stop->length=8;vm.script_begin=vm.instruction=p;return vm.update(env);
}
API(trig_word) u32 trig_word(u32 n){u32 bits;std::memcpy(&bits,n<4?static_cast<const void*>(vm.floats+n):static_cast<const void*>(code+8+(n-4)*4),4);return bits;}

API(run_random) i32 run_random(u32 op,i32 a,u32 refs,u32 seed,u32 visual_flag){
    vm={};vm.initialize();env.rate=1;vm.timer.set(0,&env.rate);vm.flags|=visual_flag;
    env.script_rng={u16(seed),0,0};env.visual_rng={54321,0,0};const i32 ints[]={23,a,0,0};const float floats[]={1.5,float(a),.125,448};std::memcpy(vm.integers,ints,sizeof ints);std::memcpy(vm.floats,floats,sizeof floats);
    std::memset(code,0,sizeof code);auto* p=reinterpret_cast<AnmInstruction*>(code);p->opcode=anm_canonical_opcode(op);p->references=refs;p->length=16;
    const i32 args[]={refs&1?(op==123?10004:10000):-3,refs&2?(op==123?10005:10001):a};for(u32 i=0;i<2;++i){if(op==123){const float f=float(args[i]);std::memcpy(code+8+i*4,&f,4);}else std::memcpy(code+8+i*4,args+i,4);}
    auto* stop=reinterpret_cast<AnmInstruction*>(code+16);stop->opcode=2;stop->length=8;vm.script_begin=vm.instruction=p;return vm.update(env);
}
API(random_seed) u32 random_seed(){return env.script_rng.seed;}
API(random_calls) u32 random_calls(){return env.script_rng.calls;}
API(visual_rng_unchanged) u32 visual_rng_unchanged(){return env.visual_rng.seed==54321&&env.visual_rng.calls==0;}

API(run_polar) i32 run_polar(float low,float high,u32 refs,u32 seed,u32 visual_flag){
    vm={};vm.initialize();env.rate=1;vm.timer.set(0,&env.rate);vm.flags|=visual_flag;
    env.script_rng={u16(seed),0,0};env.visual_rng={54321,0,0};const float floats[]={1.5,-2.75,.125,448};std::memcpy(vm.floats,floats,sizeof floats);
    std::memset(code,0,sizeof code);auto* p=reinterpret_cast<AnmInstruction*>(code);p->opcode=anm_canonical_opcode(131);p->references=refs;p->length=24;
    const float args[]={refs&1?10004.f:-3.f,refs&2?10005.f:-7.f,refs&4?10006.f:low,refs&8?10007.f:high};std::memcpy(code+8,args,sizeof args);
    auto* stop=reinterpret_cast<AnmInstruction*>(code+24);stop->opcode=2;stop->length=8;vm.script_begin=vm.instruction=p;return vm.update(env);
}

API(run_fixed_polar) i32 run_fixed_polar(float angle,float radius,u32 refs){
    vm={};vm.initialize();env.rate=1;vm.timer.set(0,&env.rate);const float floats[]={1.5,-2.75,.125,448};std::memcpy(vm.floats,floats,sizeof floats);
    std::memset(code,0,sizeof code);auto* p=reinterpret_cast<AnmInstruction*>(code);p->opcode=anm_canonical_opcode(130);p->references=refs;p->length=24;
    const float args[]={refs&1?10004.f:-3.f,refs&2?10005.f:-7.f,refs&4?10006.f:angle,refs&8?10007.f:radius};std::memcpy(code+8,args,sizeof args);
    auto* stop=reinterpret_cast<AnmInstruction*>(code+24);stop->opcode=2;stop->length=8;vm.script_begin=vm.instruction=p;return vm.update(env);
}
