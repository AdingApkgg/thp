#include "AnmStripDraw.hpp"
#include <vector>
namespace th143 {
namespace {
Matrix4 matrix(AnmView vm,u32 at){Matrix4 m;for(u32 i=0;i<16;++i)m[i]=vm.floating(at+i*4);return m;}
}
i32 draw_anm_strip(u32 manager,u32 current,AnmView vm,u32 vertices,u32 count,const AnmViewport& viewport,u32& depth_test,AnmRenderMemory& memory,AnmSpriteDevice& device,AnmMeshDevice& mesh,AnmPrimitiveDevice& upload){
    if(!vm.data)return -2;const u32 flags=vm.get(0x18);if(!(flags&1)||!(flags&2))return -1;
    if(count<2||count>0x1000000/24)return -2;
    auto read=[&](u32 p,u32& v){return memory.read_render_memory(p,&v,4);};auto write=[&](u32 p,u32 v){return memory.write_render_memory(p,&v,4);};
    u32 pending;if(!read(manager+0xbc8200,pending))return -2;if(pending&&!flush_anm_quads(manager,current,memory,device))return -2;
    const u32 depth=!(flags&0x2000);if(depth_test!=depth){if(!flush_anm_quads(current,current,memory,device))return -2;depth_test=depth;if(!device.render_state(0xe,depth))return -2;}
    auto cached=matrix_identity();for(u32 i=0;i<16;++i){vm.put(0x3e0+i*4,word(cached[i]));vm.put(0x420+i*4,word(cached[i]));}
    cached[0]=(vm.floating(0x68)*vm.floating(0x60))*cached[0];cached[5]=(vm.floating(0x6c)*vm.floating(0x64))*cached[5];vm.put(0x420,word(cached[0]));vm.put(0x434,word(cached[5]));vm.put(0x18,vm.get(0x18)&~8u);
    for(u32 axis=0;axis<3;++axis){const float angle=vm.floating(0x48+axis*4);if(angle!=0){cached=matrix_multiply(cached,matrix_rotation(axis,angle));for(u32 i=0;i<16;++i)vm.put(0x420+i*4,word(cached[i]));}}
    vm.put(0x18,vm.get(0x18)&~4u);auto world=cached;
    for(u32 i=0;i<3;++i){world[12+i]=vm.floating(0x59c+i*4)+vm.floating(0x3c+i*4);world[12+i]+=vm.floating(0x4ec+i*4);}
    if((vm.get(0x1c)&0x60000)&&!vm.get(0x594))world[12]=float(viewport.first_origin[0])+world[12];
    if(!mesh.mesh_transform(0x100,world)||!configure_anm_render(manager,current,vm,memory,device))return -2;
    u32 texture,previous;if(!read(vm.get(0x2c)+8,texture)||!read(manager+0xbc8198,previous))return -2;
    if(previous!=texture){u32 token;if(!write(manager+0xbc8198,texture)||!read(texture,token)||!device.texture(0,token))return -2;}
    if(!read(manager+0xbc81a8,previous))return -2;
    // The executable repeats the U test and does not test V in this fast path.
    if(previous!=vm.get(0x2c)||vm.floating(0x88)!=0||vm.floating(0x78)!=1.f||vm.floating(0x7c)!=1.f){
        if(!write(manager+0xbc81a8,vm.get(0x2c)))return -2;auto uv=matrix(vm,0x460);uv[8]=vm.floating(0x3b8)+vm.floating(0x88);uv[9]=vm.floating(0x3bc)+vm.floating(0x8c);uv[0]=vm.floating(0x78)*uv[0];uv[5]=vm.floating(0x7c)*uv[5];if(!mesh.mesh_transform(0x10,uv))return -2;
    }
    u8 kind;if(!memory.read_render_memory(manager+0xbc819e,&kind,1))return -2;
    if(kind!=5){if(!device.vertex_format(0x142)||!device.texture_stage_state(0,6,0)||!device.texture_stage_state(0,3,0))return -2;kind=5;if(!memory.write_render_memory(manager+0xbc819e,&kind,1))return -2;}
    u8 configured;if(!memory.read_render_memory(current+0xbc81a3,&configured,1))return -2;
    if(configured!=1){if(!device.texture_stage_state(0,4,4)||!device.texture_stage_state(0,1,4))return -2;configured=1;if(!memory.write_render_memory(current+0xbc81a3,&configured,1))return -2;}
    std::vector<u8> data(count*24);if(!memory.read_render_memory(vertices,data.data(),data.size())||!upload.primitive_upload(5,count-2,24,data.data(),data.size()))return -2;return 0;
}
bool draw_anm_effect5(u32 manager,u32 current,AnmView vm,const AnmViewport& viewport,u32& depth_test,u32& depth_write,AnmRenderMemory& memory,AnmSpriteDevice& device,AnmMeshDevice& mesh,AnmPrimitiveDevice& upload){
    auto depth=[&](u32 value){if(depth_write==value)return true;if(!flush_anm_quads(current,current,memory,device))return false;depth_write=value;return device.render_state(0x1c,value);};
    if(!depth(1))return false;const i32 result=draw_anm_strip(current,current,vm,vm.get(0x5b4),32,viewport,depth_test,memory,device,mesh,upload);if(result==-2)return false;return depth(0);
}
}
