#include "../../cpp/game/AnmManager.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include "../../cpp/game/AnmGeometry.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmVm vm{},parent{};static AnmVertex vertices[128];static AnmWorldVertex world[128];
static AnmManager manager;
struct AllocationProbe:AnmEnvironment{u32 bytes=0;bool allocate_geometry(AnmVm&,u32 size)override{bytes=size;return true;}bool update_geometry(AnmVm&)override{return true;}};
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(allocation_case) u32 allocation_case(u32 opcode,i32 count,u32 refs,u32 mode){
    vm={};vm.initialize();vm.set_drawing_mode(mode);vm.integers[0]=count;AllocationProbe env;
    struct Script{AnmInstruction command;i32 count;AnmInstruction end;} script{{i16(anm_canonical_opcode(opcode)),12,0,u16(refs)},refs?10000:count,{2,8,0,0}};
    vm.script_begin=vm.instruction=&script.command;vm.timer.set(0,&env.rate);
    return vm.update(env)<0?0:env.bytes;
}
API(mode) u32 mode(){return vm.drawing_mode();}
API(vertices_case) i32 vertices_case(u32 mode,i32 count,u32 flags,u32 color_mode,float display_scale,u32 has_parent,const float* data,i32 cycles,u32 primary,u32 secondary){
    manager.release_geometry(vm);vm={};parent={};vm.initialize();parent.initialize();
    vm.set_drawing_mode(mode);vm.flags2=flags;vm.th13_native_flags|=color_mode<<17;
    vm.integers[0]=count;vm.integers[1]=cycles;vm.color=primary;vm.secondary_color=secondary;
    std::memcpy(&vm.position,data,12);std::memcpy(&vm.script_position,data+3,12);std::memcpy(&vm.child_position,data+6,12);
    std::memcpy(&vm.rotation,data+9,12);std::memcpy(&vm.scale,data+12,8);std::memcpy(vm.floats,data+14,16);
    std::memcpy(vm.uv,data+18,16);std::memcpy(&vm.uv_offset,data+22,8);
    std::memcpy(&parent.position,data+24,12);std::memcpy(&parent.rotation,data+27,12);
    vm.parent=has_parent?&parent:nullptr;parent.flags2=0x20000;
    manager.render_space={display_scale,{320,16},{427,37}};
    const u32 size=count*2*(mode>=23?sizeof(AnmWorldVertex):sizeof(AnmVertex));
    if(!manager.allocate_geometry(vm,size)||!manager.update_geometry(vm))return -1;
    if(mode>=23)std::memcpy(world,vm.geometry,size);else std::memcpy(vertices,vm.geometry,size);
    return 0;
}
API(vertex) float vertex(u32 i,u32 field){
    const bool is_world=vm.drawing_mode()>=23;const auto p=is_world?world[i].position:vertices[i].position;
    const auto uv=is_world?world[i].uv:vertices[i].uv;
    return field==0?p.x:field==1?p.y:field==2?p.z:field==3?uv.x:field==4?uv.y:vertices[i].reciprocal_w;
}
API(color) u32 color(u32 i){return vm.drawing_mode()>=23?world[i].color:vertices[i].color;}
API(invalid_capacity) i32 invalid_capacity(){
    return vm.drawing_mode()>=23?anm_world_ring_vertices(vm,world,u32(vm.integers[0])*2-1):anm_ring_vertices(vm,vertices,u32(vm.integers[0])*2-1);
}
