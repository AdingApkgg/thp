#include "AnmExternalGeometry.hpp"
#include <vector>
namespace th143 {
i32 draw_anm_external_geometry(u32 manager,u32 current,AnmView vm,u32 vertices,u32 count,AnmRenderMemory& memory,AnmSpriteDevice& device,AnmPrimitiveDevice& upload){
    if(!vm.data)return -2;
    if(!(vm.get(0x18)&1)||!(vm.get(0x18)&2)||!vm.data[0x537])return -1;
    if(count<2||count>1000000)return -2;
    auto read=[&](u32 p,u32& v){return memory.read_render_memory(p,&v,4);};
    auto write=[&](u32 p,u32 v){return memory.write_render_memory(p,&v,4);};
    u32 pending;if(!read(manager+0xbc8200,pending))return -2;
    if(pending&&!flush_anm_quads(manager,current,memory,device))return -2;
    u32 pointer,previous;
    if(!read(vm.get(0x2c)+8,pointer)||!read(manager+0xbc8198,previous))return -2;
    if(previous!=pointer){u32 texture;if(!write(manager+0xbc8198,pointer)||!read(pointer,texture)||!device.texture(0,texture))return -2;}
    u8 kind;if(!memory.read_render_memory(manager+0xbc819e,&kind,1))return -2;
    if(kind!=3){
        if(!device.vertex_format(0x144)||!device.texture_stage_state(0,6,0)||!device.texture_stage_state(0,3,0))return -2;
        kind=3;if(!memory.write_render_memory(manager+0xbc819e,&kind,1))return -2;
    }
    if(!configure_anm_render(manager,current,vm,memory,device))return -2;
    u8 configured;if(!memory.read_render_memory(current+0xbc81a3,&configured,1))return -2;
    if(configured!=1){
        if(!device.texture_stage_state(0,4,4)||!device.texture_stage_state(0,1,4))return -2;
        configured=1;if(!memory.write_render_memory(current+0xbc81a3,&configured,1))return -2;
    }
    std::vector<u8> data(count*28);
    if(!memory.read_render_memory(vertices,data.data(),u32(data.size()))||!upload.primitive_upload(5,count-2,28,data.data(),u32(data.size())))return -2;
    return 0;
}
}
