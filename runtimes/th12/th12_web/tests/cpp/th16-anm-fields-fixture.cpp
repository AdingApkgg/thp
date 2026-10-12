#include "../../cpp/game/AnmVm.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmVm vm{};
struct Environment:AnmEnvironment{
    u32 calls=0;
    u32 allocation_bytes=0;
    bool th16_mode10(AnmVm&)override{++calls;return true;}
    bool update_geometry(AnmVm&)override{return true;}
    bool screen_uv(AnmVm&)override{return true;}
    bool allocate_geometry(AnmVm& vm,u32 bytes)override{allocation_bytes=bytes;vm.geometry=this;return true;}
};
static Environment env;
alignas(4) static u8 code[64];
static u32 initial_flags;
static u32 last_opcode;
static AnmResource resource;
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(open_resource) i32 open_resource(const u8* p,u32 n){return resource.open(p,n)?i32(resource.scripts.size()):-i32(resource.last_error);}
API(resource_error) const char* resource_error(){return resource.detail.c_str();}
API(canonical) u32 canonical(u32 op){return anm_canonical_opcode(u16(op));}
API(run) i32 run(u32 opcode,i32 value,i32 second,u32 native_flags,u32 native_flags2,u32 refs){
    last_opcode=opcode;
    vm={};vm.initialize();env.rate=1;env.calls=0;vm.timer.set(0,&env.rate);
    vm.th13_native_flags=native_flags;vm.flags=0x04100007u;
    vm.set_drawing_mode((native_flags>>25)&31u);
    vm.flags=(vm.flags&~0x70u)|(((native_flags>>5)&7u)<<4);
    vm.flags=(vm.flags&~0x3c0000u)|(((native_flags>>21)&15u)<<18);
    vm.integers[0]=value;vm.integers[1]=second;vm.flags2=native_flags2;vm.layer=27;initial_flags=vm.flags;
    std::memset(code,0,sizeof code);auto* p=reinterpret_cast<AnmInstruction*>(code);
    p->opcode=anm_canonical_opcode(opcode);p->length=opcode==312?16:12;p->references=refs;
    if(refs&1)value=10000;if(refs&2)second=10001;
    std::memcpy(code+8,&value,4);std::memcpy(code+12,&second,4);
    auto* next=reinterpret_cast<AnmInstruction*>(code+p->length);next->time=32760;next->length=8;
    vm.script_begin=vm.instruction=p;return vm.update(env);
}
API(word) u32 word(u32 n){
    switch(n){
    case 0:return (vm.th13_native_flags&~0x3fe001e0u)|(vm.drawing_mode()<<25)|(vm.blend_mode()<<5)|(((vm.flags>>18)&15u)<<21);
    case 1:return vm.flags2;
    case 2:return vm.layer;
    case 3:return vm.instruction?u32(reinterpret_cast<u8*>(vm.instruction)-code):0;
    case 4:return env.calls;
    case 5:return vm.flags&~(0x3fc0070u|(last_opcode==310?1u:0u));
    case 6:return initial_flags&~(0x3fc0070u|(last_opcode==310?1u:0u));
    default:return 0;
    }
}
API(run_shape) i32 run_shape(u32 op,u32 native_flags,i32 value,i32 second,u32 refs){
    vm={};vm.initialize();env.rate=1;vm.timer.set(0,&env.rate);vm.th13_native_flags=native_flags;vm.set_drawing_mode((native_flags>>25)&31);
    vm.integers[0]=-257;vm.sprite_size.y=-2.5;
    const float floats[]={-1.25,.125,448,-99};std::memcpy(vm.floats,floats,sizeof floats);
    std::memset(code,0,sizeof code);auto* p=reinterpret_cast<AnmInstruction*>(code);p->opcode=anm_canonical_opcode(op);p->length=op==611?20:16;p->references=refs;
    const float first=refs&1?10004.f:float(value);std::memcpy(code+8,&first,4);
    if(op==604||op==605){const i32 v=refs&2?10000:second;std::memcpy(code+12,&v,4);}else{const float v=refs&2?10005.f:float(second);std::memcpy(code+12,&v,4);}
    if(op==611){const i32 count=refs&4?10000:16;std::memcpy(code+16,&count,4);}
    auto* stop=reinterpret_cast<AnmInstruction*>(code+p->length);stop->opcode=2;stop->length=8;vm.script_begin=vm.instruction=p;return vm.update(env);
}
API(shape_word) u32 shape_word(u32 n){if(!n)return (vm.th13_native_flags&~0x3e000000u)|(vm.drawing_mode()<<25);if(n==3)return u32(vm.integers[0]);u32 bits;const float value=n==1?vm.sprite_size.x:vm.sprite_size.y;std::memcpy(&bits,&value,4);return bits;}
API(run_flip) i32 run_flip(u32 op,u32 flags,u32 value_bits){
    vm={};vm.initialize();env.rate=1;vm.timer.set(0,&env.rate);vm.th13_native_flags=flags;vm.flags=7|(flags&8)|((flags&0x1800)>>2);std::memcpy(&vm.scale.x,&value_bits,4);vm.scale.y=-2.5;
    std::memset(code,0,sizeof code);auto* p=reinterpret_cast<AnmInstruction*>(code);p->opcode=anm_canonical_opcode(op);p->length=8;auto* stop=reinterpret_cast<AnmInstruction*>(code+8);stop->opcode=2;stop->length=8;vm.script_begin=vm.instruction=p;return vm.update(env);
}
API(flip_word) u32 flip_word(u32 n){if(!n)return (vm.th13_native_flags&~0x1808u)|((vm.flags&0x600u)<<2)|(vm.flags&8);u32 bits;const float value=n==1?vm.scale.x:vm.scale.y;std::memcpy(&bits,&value,4);return bits;}
API(run_pivot) i32 run_pivot(i32 value,i32 second,u32 refs){
    vm={};vm.initialize();env.rate=1;vm.timer.set(0,&env.rate);vm.th13_native_flags=0xab123457;vm.flags2=0x78345678;
    const float floats[]={-1.25,.125,448,-99};std::memcpy(vm.floats,floats,sizeof floats);
    std::memset(code,0,sizeof code);auto* p=reinterpret_cast<AnmInstruction*>(code);p->opcode=anm_canonical_opcode(436);p->length=16;p->references=refs;const float args[]={refs&1?10004.f:float(value),refs&2?10005.f:float(second)};std::memcpy(code+8,args,sizeof args);
    auto* stop=reinterpret_cast<AnmInstruction*>(code+16);stop->opcode=2;stop->length=8;vm.script_begin=vm.instruction=p;return vm.update(env);
}
API(pivot_word) u32 pivot_word(u32 n){if(n==2)return vm.th13_native_flags;if(n==3)return vm.flags2;u32 bits;const float value=n?vm.pivot.y:vm.pivot.x;std::memcpy(&bits,&value,4);return bits;}
API(run_ring) i32 run_ring(u32 op,u32 flags,i32 value,u32 refs){
    vm={};vm.initialize();env.rate=1;env.allocation_bytes=0;vm.timer.set(0,&env.rate);vm.th13_native_flags=flags;vm.set_drawing_mode((flags>>25)&31);vm.integers[0]=value;
    std::memset(code,0,sizeof code);auto* p=reinterpret_cast<AnmInstruction*>(code);p->opcode=anm_canonical_opcode(op);p->length=12;p->references=refs;const i32 arg=refs?10000:value;std::memcpy(code+8,&arg,4);auto* stop=reinterpret_cast<AnmInstruction*>(code+12);stop->opcode=2;stop->length=8;vm.script_begin=vm.instruction=p;return vm.update(env);
}
API(ring_word) u32 ring_word(u32 n){if(!n)return (vm.th13_native_flags&~0x3e000000u)|(vm.drawing_mode()<<25);return n==1?env.allocation_bytes:vm.geometry==&env;}
