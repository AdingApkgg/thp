#include "AnmRectDraw.hpp"
#include <cmath>
namespace th143 {
namespace {
bool rectangle(u32 manager,u32 current,float x,float y,float width,float height,float angle,u32 left,u32 right,u32 ax,u32 ay,u32& depth,AnmRenderMemory& memory,AnmSpriteDevice& device,AnmPrimitiveDevice& upload){
    u32 cursor;if(!memory.read_render_memory(manager+0xfe8210,&cursor,4))return false;if(cursor+80>=manager+0xfe8210)return true;
    if(ax>2||ay>2||!flush_anm_quads(manager,current,memory,device))return false;
    const float cosine=float(std::cos(double(angle))),sine=float(std::sin(double(angle)));
    const float min_x=ax==0?width*-.5f:ax==1?0.f:-width,max_x=ax==0?width*.5f:ax==1?width:0.f;
    const float min_y=ay==0?height*-.5f:ay==1?0.f:-height,max_y=ay==0?height*.5f:ay==1?height:0.f;
    const std::array<float,4> xs{min_x,max_x,min_x,max_x},ys{min_y,min_y,max_y,max_y};std::array<u8,80> data{};
    for(u32 i=0;i<4;++i){AnmView v{data.data()+i*20};float vx=xs[i]*cosine-ys[i]*sine;vx+=x;float vy=ys[i]*cosine+xs[i]*sine;vy+=y;v.put(0,word(vx));v.put(4,word(vy));v.put(8,0);v.put(12,word(1.f));v.put(16,i&1?right:left);}
    if(!memory.write_render_memory(cursor,data.data(),80))return false;
    if(depth){if(!flush_anm_quads(current,current,memory,device))return false;depth=0;if(!device.render_state(0xe,0))return false;}
    u8 configured;if(!memory.read_render_memory(current+0xbc81a3,&configured,1))return false;
    if(configured){if(!device.texture_stage_state(0,4,3)||!device.texture_stage_state(0,1,3))return false;configured=0;if(!memory.write_render_memory(current+0xbc81a3,&configured,1))return false;}
    u8 kind;if(!memory.read_render_memory(manager+0xbc819e,&kind,1))return false;
    if(kind!=1){if(!device.texture_stage_state(0,6,0)||!device.texture_stage_state(0,3,0))return false;kind=1;if(!memory.write_render_memory(manager+0xbc819e,&kind,1))return false;}
    if(!device.vertex_format(0x44)||!upload.primitive_upload(5,2,20,data.data(),80))return false;
    cursor+=80;u32 draws;if(!memory.write_render_memory(manager+0xfe8210,&cursor,4)||!memory.read_render_memory(manager+0xcc,&draws,4))return false;++draws;return memory.write_render_memory(manager+0xcc,&draws,4);
}
}
bool draw_anm_rectangle(u32 manager,u32 current,float x,float y,float width,float height,float angle,u32 left,u32 right,u32 ax,u32 ay,bool outlined,u32& depth,AnmRenderMemory& memory,AnmSpriteDevice& device,AnmPrimitiveDevice& upload){
    if(outlined){const u32 a=(left&0xffffff)|((left>>1)&0x7f000000),b=(right&0xffffff)|((right>>1)&0x7f000000);if(!rectangle(manager,current,x,y,width+1.f,height+1.f,angle,a,b,ax,ay,depth,memory,device,upload))return false;}
    return rectangle(manager,current,x,y,width,height,angle,left,right,ax,ay,depth,memory,device,upload);
}
i32 draw_anm_rect_sprite(u32 manager,u32 current,AnmView vm,const AnmViewport& viewport,u32& depth,AnmRenderMemory& memory,AnmSpriteDevice& device,AnmPrimitiveDevice& upload,AnmTransformHost& host){
    if(!vm.data)return -2;const u32 mode=(vm.get(0x18)>>25)&31;if(mode!=16&&mode!=20&&mode!=21&&mode!=22)return -2;
    float angle=vm.floating(0x50),width=vm.floating(0x80)*vm.floating(0x60),height=vm.floating(0x84)*vm.floating(0x64);std::array<float,3> position;
    if(!anm_position(vm,viewport,host,position))return -2;
    if(vm.get(0x594)&&!(vm.get(0x1c)&0x8000)){auto parent=host.transform_parent(vm.get(0x594));if(!parent.data)return -2;width=parent.floating(0x60)*width;height=parent.floating(0x64)*height;angle=parent.floating(0x50)+angle;}
    if(!configure_anm_render(manager,current,vm,memory,device))return -2;
    const u32 viewport_mode=(vm.get(0x1c)>>19)&7;if(viewport_mode==1||viewport_mode==2){const float scale=viewport_mode==2?viewport.scale*.5f:viewport.scale;width=scale*width;height=scale*height;}
    const u32 left=vm.get(0x534),right=vm.get(mode==20||mode==22?0x538:0x534),ax=(vm.get(0x18)>>21)&3,ay=(vm.get(0x18)>>23)&3;
    return draw_anm_rectangle(manager,current,position[0],position[1],width,height,angle,left,right,ax,ay,mode>=21,depth,memory,device,upload)?0:-2;
}
}
