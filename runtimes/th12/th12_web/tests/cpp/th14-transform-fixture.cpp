#include "../../cpp/game/AnmVm.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmVm vm;
static AnmEnvironment env;
alignas(4) static u8 code[128];
API(begin_case) void begin_case(u32 op,u32 refs,u32 count,u32 a,u32 b,u32 c,u32 d,u32 e,u32 f,u32 g,u32 h,u32 i,u32 j,float x,float y,float z){
    vm={};vm.initialize();env.rate=1;vm.timer.set(0,&env.rate);vm.flags2=0x800000;
    vm.color=0xab123456;vm.secondary_color=0x78345678;
    vm.extra_scale={1.25f,.75f};vm.texture_scale={1.5f,.5f};vm.pivot={3.25f,-5};
    vm.floats[0]=x;vm.floats[1]=y;vm.floats[2]=z;vm.floats[3]=.125f;
    const i32 ints[]={8,37,201,77};std::memcpy(vm.integers,ints,sizeof(ints));
    vm.script_position={3,5,8};vm.position={11.25f,-7.5f,10};
    std::memset(code,0,sizeof(code));auto* command=reinterpret_cast<AnmInstruction*>(code);
    command->opcode=anm_canonical_opcode(op);command->length=8+count*4;command->references=refs;
    const u32 args[]={a,b,c,d,e,f,g,h,i,j};std::memcpy(code+8,args,count*4);
    auto* next=reinterpret_cast<AnmInstruction*>(code+command->length);next->length=8;next->time=30000;
    vm.script_begin=vm.instruction=command;
}
API(tick) i32 tick(){return vm.update(env);}
API(value) float value(u32 i){
    const float values[]={vm.extra_scale.x,vm.extra_scale.y,vm.texture_scale.x,vm.texture_scale.y,
        vm.pivot.x,vm.pivot.y,vm.scroll_velocity.x,vm.scroll_velocity.y,
        vm.script_position.x,vm.script_position.y,vm.script_position.z,
        vm.position.x,vm.position.y,vm.position.z,vm.rotation.x,vm.rotation.y,vm.rotation.z,
        vm.scale.x,vm.scale.y,vm.uv_offset.x,vm.uv_offset.y,vm.timer.fractional,
        vm.sprite_size.x,vm.sprite_size.y,float(vm.drawing_mode()),float(vm.integers[0])};
    return values[i];
}
API(word) u32 word(u32 i){return i?vm.secondary_color:vm.color;}
