#include "AnmFanDraw.hpp"
#include "DirectionVector.hpp"
#include <vector>
namespace th143 {
i32 draw_anm_geometry_sprite(u32 manager,u32 current,AnmView vm,u32& depth,AnmRenderMemory& memory,AnmSpriteDevice& device,AnmPrimitiveDevice& upload,AnmSpriteDrawHost& host){
    if(!vm.data)return -2;if(vm.get(0x5bc)&&!host.draw_callback(vm.get(0x5bc),vm))return -2;
    if(!(vm.get(0x18)&1)||!(vm.get(0x18)&2)||(vm.get(0x1c)&0x20))return -1;
    if(depth){if(!flush_anm_quads(current,current,memory,device))return -2;depth=0;if(!device.render_state(14,0))return -2;}
    const u32 mode=(vm.get(0x18)>>25)&31;const bool fan=mode==11;if(!fan&&mode!=9&&mode!=12&&mode!=13&&mode!=14)return -2;
    if(!fan&&!vm.data[0x537])return -1;const u32 count=vm.get(0x4ac)*2;if(count<2||count>1000000)return -2;
    auto read=[&](u32 p,u32& v){return memory.read_render_memory(p,&v,4);};auto write=[&](u32 p,u32 v){return memory.write_render_memory(p,&v,4);};
    u32 pending;if(!read(manager+0xbc8200,pending))return -2;if(pending&&!flush_anm_quads(manager,current,memory,device))return -2;
    auto kind=[&](){u8 value;if(!memory.read_render_memory(manager+0xbc819e,&value,1))return false;if(value!=3){if(!device.vertex_format(0x144))return false;if(!fan&&(!device.texture_stage_state(0,6,0)||!device.texture_stage_state(0,3,0)))return false;value=3;if(!memory.write_render_memory(manager+0xbc819e,&value,1))return false;}return true;};
    auto texture=[&](){u32 pointer,previous;if(!read(vm.get(0x2c)+8,pointer)||!read(manager+0xbc8198,previous))return false;if(previous!=pointer){u32 token;if(!write(manager+0xbc8198,pointer)||!read(pointer,token)||!device.texture(0,token))return false;}return true;};
    if(fan){if(!kind()||!configure_anm_render(manager,current,vm,memory,device)||!texture())return -2;
        u8 value;if(!memory.read_render_memory(manager+0xbc819e,&value,1))return -2;if(value!=1){if(!device.texture_stage_state(0,6,0)||!device.texture_stage_state(0,3,0))return -2;value=1;if(!memory.write_render_memory(manager+0xbc819e,&value,1))return -2;}
    }else{if(!texture()||!kind()||!configure_anm_render(manager,current,vm,memory,device))return -2;
        u8 configured;if(!memory.read_render_memory(current+0xbc81a3,&configured,1))return -2;if(configured!=1){if(!device.texture_stage_state(0,4,4)||!device.texture_stage_state(0,1,4))return -2;configured=1;if(!memory.write_render_memory(current+0xbc81a3,&configured,1))return -2;}
    }
    std::vector<u8> data(count*28);if(!memory.read_render_memory(vm.get(0x5b4),data.data(),data.size())||!upload.primitive_upload(fan?6:5,count-2,28,data.data(),data.size()))return -2;return 0;
}
i32 draw_anm_fan_sprite(u32 manager,u32 current,AnmView vm,const AnmViewport& viewport,u32& depth,AnmRenderMemory& memory,AnmSpriteDevice& device,AnmPrimitiveDevice& upload,AnmSpriteDrawHost& host){
    if(!vm.data)return -2;if(vm.get(0x5bc)&&!host.draw_callback(vm.get(0x5bc),vm))return -2;
    if(!(vm.get(0x18)&1)||!(vm.get(0x18)&2)||(vm.get(0x1c)&0x20))return -1;
    if(depth){if(!flush_anm_quads(current,current,memory,device))return -2;depth=0;if(!device.render_state(14,0))return -2;}
    if(((vm.get(0x18)>>25)&31)!=17)return -2;
    float radius=vm.floating(0x80)*vm.floating(0x60),angle=vm.floating(0x50);std::array<float,3> position;
    if(!anm_position(vm,viewport,host,position))return -2;
    if(vm.get(0x594)&&!(vm.get(0x1c)&0x8000)){auto parent=host.transform_parent(vm.get(0x594));if(!parent.data)return -2;radius=parent.floating(0x60)*radius;angle=parent.floating(0x50)+angle;}
    const u32 mode=(vm.get(0x1c)>>19)&7;if(mode==1||mode==2){const float scale=mode==2?viewport.scale*.5f:viewport.scale;radius=scale*radius;}
    if(!configure_anm_render(manager,current,vm,memory,device))return -2;
    const u32 count=vm.get(0x4ac);if(signed_word(count)<0||count>1000000)return -2;
    const u32 bytes=(count+2)*20;u32 cursor;if(!memory.read_render_memory(manager+0xfe8210,&cursor,4))return -2;
    if(std::uint64_t(cursor)+bytes>=std::uint64_t(manager)+0xfe8210)return 0;
    if(!flush_anm_quads(manager,current,memory,device))return -2;
    std::vector<u8> data(bytes);auto vertex=[&](u32 i,float x,float y,u32 color){auto v=AnmView{data.data()+i*20};v.put(0,word(x));v.put(4,word(y));v.put(8,0);v.put(12,word(1.f));v.put(16,color);};
    vertex(0,position[0],position[1],vm.get(0x534));const float tau=real(0x40c90fdb),step=tau/float(signed_word(count));
    for(u32 i=0;i<=count;++i){DirectionVector p;if(!direction_vector(angle,radius,p))return -2;vertex(i+1,p.x+position[0],p.y+position[1],vm.get(0x538));angle+=step;
        u32 n=0;while(angle>real(0x40490fdb)){angle-=tau;if(n++>32)break;}while(real(0xc0490fdb)>angle){angle+=tau;if(n++>32)break;}
    }
    if(!memory.write_render_memory(cursor,data.data(),bytes))return -2;
    if(depth){if(!flush_anm_quads(current,current,memory,device))return -2;depth=0;if(!device.render_state(14,0))return -2;}
    if(!flush_anm_quads(current,current,memory,device)||!device.render_state(23,8))return -2;
    u8 configured;if(!memory.read_render_memory(current+0xbc81a3,&configured,1))return -2;
    if(configured){if(!device.texture_stage_state(0,4,3)||!device.texture_stage_state(0,1,3))return -2;configured=0;if(!memory.write_render_memory(current+0xbc81a3,&configured,1))return -2;}
    u8 kind;if(!memory.read_render_memory(manager+0xbc819e,&kind,1))return -2;
    if(kind!=1){if(!device.texture_stage_state(0,6,0)||!device.texture_stage_state(0,3,0))return -2;kind=1;if(!memory.write_render_memory(manager+0xbc819e,&kind,1))return -2;}
    if(!device.vertex_format(0x44)||!upload.primitive_upload(6,count,20,data.data(),bytes))return -2;
    cursor+=bytes;u32 draws;if(!memory.write_render_memory(manager+0xfe8210,&cursor,4)||!memory.read_render_memory(manager+0xcc,&draws,4))return -2;++draws;return memory.write_render_memory(manager+0xcc,&draws,4)?0:-2;
}
}
