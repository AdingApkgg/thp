#include "AnmMeshDraw.hpp"
#include "DirectionVector.hpp"
namespace th143 {
namespace {
u32 tint(u32 color,u32 factor){u32 out=0;for(u32 i=0;i<4;++i){const u32 v=((color>>(i*8)&255)*(factor>>(i*8)&255))>>7;out|=(v<256?v:255)<<(i*8);}return out;}
bool inherit(AnmView vm,const AnmViewport& viewport,AnmTransformHost& host,std::array<float,3>& out){const u32 flags=vm.get(0x1c),mode=(flags>>19)&7;
    if(mode>=1&&mode<=4){const float scale=(mode==2||mode==4)?viewport.scale*.5f:viewport.scale;for(auto& f:out)f*=scale;}
    if(vm.get(0x594)&&!(flags&0x8000)){auto parent=host.transform_parent(vm.get(0x594));if(!parent.data)return false;if(flags&0x400000){DirectionVector angle;if(!direction_vector(parent.floating(0x50),1.f,angle))return false;const float x=out[0],y=out[1];out[0]=x*angle.x-y*angle.y;out[1]=y*angle.x+x*angle.y;}
        std::array<float,3> origin;if(!anm_position(parent,viewport,host,origin))return false;for(u32 i=0;i<3;++i)out[i]+=origin[i];
    }else{const u32 origin=(flags>>17)&3;if(origin){const auto& p=origin==1?viewport.first_origin:viewport.second_origin;out[0]+=float(p[0]);out[1]+=float(p[1]);}}return true;
}
Matrix4 matrix(AnmView s,u32 at){Matrix4 out;for(u32 i=0;i<16;++i)out[i]=s.floating(at+i*4);return out;}
}
i32 draw_anm_mesh(u32 manager,u32 current,AnmView vm,const AnmViewport& viewport,u32& depth_test,AnmRenderMemory& memory,AnmSpriteDevice& device,AnmMeshDevice& mesh,AnmTransformHost& host){
    if(!vm.data)return -2;u32 flags=vm.get(0x18);if(!(flags&1)||!(flags&2)||!vm.data[0x537])return -1;
    auto read=[&](u32 p,u32& v){return memory.read_render_memory(p,&v,4);};auto write=[&](u32 p,u32 v){return memory.write_render_memory(p,&v,4);};
    u32 pending;if(!read(manager+0xbc8200,pending))return -2;if(pending&&!flush_anm_quads(manager,current,memory,device))return -2;
    const u32 depth=!(flags&0x2000);if(depth_test!=depth){if(!flush_anm_quads(current,current,memory,device))return -2;depth_test=depth;if(!device.render_state(0xe,depth))return -2;}
    if(!(flags&0x10000)&&(flags&0xc)){auto cached=matrix(vm,0x3e0);cached[0]=(vm.floating(0x68)*vm.floating(0x60))*cached[0];cached[5]=(vm.floating(0x6c)*vm.floating(0x64))*cached[5];
        for(u32 i=0;i<16;++i)vm.put(0x420+i*4,word(cached[i]));vm.put(0x18,vm.get(0x18)&~8u);
        const u32 mode=(vm.get(0x1c)>>19)&7;if(mode==1||mode==2){const float scale=mode==2?viewport.scale*.5f:viewport.scale;cached[0]*=scale;cached[5]*=scale;vm.put(0x420,word(cached[0]));vm.put(0x434,word(cached[5]));}
        const u32 order=(vm.get(0x1c)>>2)&7;static constexpr u32 axes[6][3]={{0,1,2},{0,2,1},{1,0,2},{1,2,0},{2,0,1},{2,1,0}};
        if(order<6)for(u32 axis:axes[order]){const float angle=vm.floating(0x48+axis*4);if(angle!=0){cached=matrix_multiply(cached,matrix_rotation(axis,angle));for(u32 i=0;i<16;++i)vm.put(0x420+i*4,word(cached[i]));}}
        vm.put(0x18,vm.get(0x18)&~4u);
    }
    auto world=matrix(vm,0x420);std::array<float,3> position={world[12],world[13],world[14]};
    position[0]=vm.floating(0x59c)+vm.floating(0x3c);position[0]+=vm.floating(0x4ec);float pivot=vm.floating(0x90)*vm.floating(0x60);pivot*=vm.floating(0x68);position[0]-=pivot;
    position[1]=vm.floating(0x5a0)+vm.floating(0x40);position[1]+=vm.floating(0x4f0);pivot=vm.floating(0x94)*vm.floating(0x64);pivot*=vm.floating(0x6c);position[1]-=pivot;
    if(!inherit(vm,viewport,host,position)||!configure_anm_render(manager,current,vm,memory,device))return -2;for(u32 i=0;i<3;++i)world[12+i]=position[i];
    u32 color=vm.get((vm.get(0x18)&0x60000)?0x538:0x534),enabled,factor;if(!read(manager+0xff75a8,enabled)||!read(manager+0xff75a4,factor))return -2;if(enabled)color=tint(color,factor);
    u32 previous;if(!read(manager+0xbc8194,previous))return -2;if(previous!=color){if(!flush_anm_quads(manager,current,memory,device)||!write(manager+0xbc8194,color)||!device.render_state(0x3c,color))return -2;}
    world[14]=vm.floating(0x5a4)+vm.floating(0x44);world[14]+=vm.floating(0x4f4);if(!mesh.mesh_transform(0x100,world))return -2;
    u32 texture;if(!read(vm.get(0x2c)+8,texture)||!read(manager+0xbc8198,previous))return -2;if(previous!=texture){u32 token;if(!write(manager+0xbc8198,texture)||!read(texture,token)||!device.texture(0,token))return -2;}
    if(!read(manager+0xbc81a8,previous))return -2;
    // Original tests U scroll twice; V scroll does not invalidate this cache.
    if(previous!=vm.get(0x2c)||vm.floating(0x88)!=0||vm.floating(0x78)!=1.f||vm.floating(0x7c)!=1.f){
        if(!write(manager+0xbc81a8,vm.get(0x2c)))return -2;auto texture_matrix=matrix(vm,0x460);texture_matrix[8]=vm.floating(0x3b8)+vm.floating(0x88);texture_matrix[9]=vm.floating(0x3bc)+vm.floating(0x8c);texture_matrix[0]=vm.floating(0x78)*texture_matrix[0];texture_matrix[5]=vm.floating(0x7c)*texture_matrix[5];if(!mesh.mesh_transform(0x10,texture_matrix))return -2;
    }
    u8 kind;if(!memory.read_render_memory(manager+0xbc819e,&kind,1))return -2;if(kind!=2){u32 buffer;if(!read(manager+0xbc81ac,buffer)||!mesh.mesh_stream(0,buffer,0,20)||!device.vertex_format(0x102)||!device.texture_stage_state(0,6,3)||!device.texture_stage_state(0,3,3))return -2;kind=2;if(!memory.write_render_memory(manager+0xbc819e,&kind,1))return -2;}
    u8 configured;if(!memory.read_render_memory(current+0xbc81a3,&configured,1))return -2;if(configured!=1){if(!device.texture_stage_state(0,4,4)||!device.texture_stage_state(0,1,4))return -2;configured=1;if(!memory.write_render_memory(current+0xbc81a3,&configured,1))return -2;}
    const u32 ax=(vm.get(0x18)>>21)&3,ay=(vm.get(0x18)>>23)&3;if(!mesh.mesh_primitive(5,(ay*3+ax)*4,2))return -2;return 0;
}
}
