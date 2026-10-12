// Small fixture for the shared interpreter; no gameplay or rendering substitutes.
#include "../../cpp/game/AnmVm.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmVm vm{};
#if PORT_TITLE == 14
// This probe compares handler state at the native next-dispatch boundary.
// Geometry is verified independently through AnmManager in th14-rings-check.
struct StateEnvironment:AnmEnvironment{bool update_geometry(AnmVm&)override{return true;}};
static StateEnvironment env;
#else
static AnmEnvironment env;
#endif
alignas(4) static u8 code[64];
API(run) int run(u32 opcode,i32 value,u32 variant,u32 references,i32 argument,i32 argument2){
    vm={};vm.initialize();env.rate=1;vm.timer.set(0,&env.rate);
    vm.flags=7|(variant?0x400:0);vm.flags2=kPortTitle==14?(variant?0xbc0000:0x820000):(variant?0x840000:0x800000);
    vm.th13_native_flags=variant?0xc0008000:0x40000000;
    vm.layer=27;vm.color=0xab123456;vm.secondary_color=0x78345678;
    vm.scale={1,-2.5};vm.integers[0]=value;vm.integers[1]=value^2;
    std::memset(code,0,sizeof(code));
    auto* command=reinterpret_cast<AnmInstruction*>(code);
    const u32 size=opcode==312?16:12;
    command->opcode=anm_canonical_opcode(opcode);command->length=size;command->references=references;
    std::memcpy(code+8,&argument,4);
    std::memcpy(code+12,&argument2,4);
    auto* next=reinterpret_cast<AnmInstruction*>(code+size);next->length=8;next->time=32760;
    auto* end=reinterpret_cast<AnmInstruction*>(code+size+8);end->opcode=-1;end->length=8;end->time=32767;
    vm.script_begin=vm.instruction=command;
    return vm.update(env);
}
API(next_update) int next_update(){return vm.update(env);}
API(word) u32 word(u32 field){
    switch(field){
    case 0:return vm.instruction==nullptr;
    case 1:return vm.color;
    case 2:return vm.secondary_color;
    case 3:return vm.layer;
    case 4:return vm.flags2;
    case 5:return (vm.flags&0x400)!=0;
    case 6:return (vm.flags&1)!=0;
    case 7:return (vm.flags&8)!=0;
    case 8:return (vm.th13_native_flags&0x8000)!=0;
    case 9:return vm.th13_native_flags>>30;
    case 10:return vm.drawing_mode();
    case 11:return (vm.th13_native_flags>>17)&3;
    case 12:return vm.blend_mode();
    case 13:return (vm.flags&0x800)!=0;
    case 14:return (vm.flags&0x200)!=0;
    case 15:return (vm.flags>>18)&3;
    case 16:return (vm.flags>>20)&3;
    default:return 0;
    }
}
API(real) float real(u32 field){return field==0?vm.scale.y:field==1?vm.timer.fractional:vm.scale.x;}
API(canonical) u32 canonical(u32 op){return anm_canonical_opcode(op);}
API(run_polar) int run_polar(u32 seed,float low,float high,u32 refs,u32 visual){
    vm={};vm.initialize();env.rate=1;vm.timer.set(0,&env.rate);
    env.script_rng={u16(seed),0,0};env.visual_rng={54321,0,0};
    vm.flags=7|(visual?0x40000000:0);vm.floats[0]=low;vm.floats[3]=high;
    std::memset(code,0,sizeof(code));
    auto* command=reinterpret_cast<AnmInstruction*>(code);
    command->opcode=anm_canonical_opcode(131);command->length=24;command->references=refs;
    const float args[]={10005.f,10006.f,(refs&4)?10004.f:low,(refs&8)?10007.f:high};
    std::memcpy(code+8,args,sizeof(args));
    auto* next=reinterpret_cast<AnmInstruction*>(code+24);next->length=8;next->time=32760;
    auto* end=reinterpret_cast<AnmInstruction*>(code+32);end->opcode=-1;end->length=8;end->time=32767;
    vm.script_begin=vm.instruction=command;
    return vm.update(env);
}
API(polar_real) float polar_real(u32 i,u32 refs){
    if(refs&(1u<<i))return vm.floats[i+1];
    float result;std::memcpy(&result,code+8+i*4,4);return result;
}
API(rng_word) u32 rng_word(u32 i){return i==0?env.script_rng.seed:i==1?env.script_rng.calls:env.visual_rng.calls;}
API(allocate) void* allocate(u32 size){return std::malloc(size);}
API(release) void release(void* p){std::free(p);}
API(open_resource) i32 open_resource(const u8* data,u32 size){
    AnmResource resource;
    return resource.open(data,size)?i32(resource.scripts.size()):-resource.last_error;
}
