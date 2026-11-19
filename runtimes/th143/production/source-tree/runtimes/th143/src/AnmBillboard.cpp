#include "AnmBillboard.hpp"
#include <cmath>
namespace th143 {
namespace {
u32 tint(u32 color,u32 factor){u32 out=0;for(u32 i=0;i<4;++i){const u32 v=((color>>(i*8)&255)*(factor>>(i*8)&255))>>7;out|=(v<256?v:255)<<(i*8);}return out;}
u32 trunc(float value){return value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000;}
u32 fade_color(u32 color,AnmView camera,float weight,bool cubic){u32 result=0;for(u32 i=0;i<3;++i){const u32 channel=(color>>(i*8))&255;const i32 delta=signed_word(channel-trunc(camera.floating(0x118+i*4)));const float amount=float(delta)*weight;result|=((channel-trunc(amount))&255)<<(i*8);}
    float alpha_weight=weight;if(cubic){alpha_weight*=weight;alpha_weight*=weight;}alpha_weight=1.f-alpha_weight;const float alpha=alpha_weight*float(color>>24);return result|((trunc(alpha)&255)<<24);
}
}
i32 build_anm_billboard(AnmView vm,AnmView camera,AnmQuad& quad){
    if(!vm.data||!camera.data)return -2;auto world=matrix_identity();for(u32 i=0;i<3;++i){world[12+i]=vm.floating(0x59c+i*4)+vm.floating(0x3c+i*4);world[12+i]+=vm.floating(0x4ec+i*4);}
    const StageVector zero{};const auto center=project_stage_point(camera,world,zero);if(center[2]<0||center[2]>1)return -1;
    StageVector side;for(u32 i=0;i<3;++i)side[i]=camera.floating(0x30+i*4);const auto second=project_stage_point(camera,world,side);StageVector delta;for(u32 i=0;i<3;++i)delta[i]=second[i]-center[i];
    float squared=delta[1]*delta[1]+delta[0]*delta[0];squared+=delta[2]*delta[2];float factor=float(std::sqrt(double(squared)));factor*=.5f;
    float width=vm.floating(0x80)*factor;float height=vm.floating(0x84)*factor;width*=vm.floating(0x60);height*=vm.floating(0x64);width*=vm.floating(0x68);height*=vm.floating(0x6c);
    const u32 ax=(vm.get(0x18)>>21)&3,ay=(vm.get(0x18)>>23)&3;if(ax>2||ay>2)return -2;
    const float left=ax==0?width*-.5f:ax==1?0.f:-width,right=ax==0?width*.5f:ax==1?width:0.f;
    const float top=ay==0?height*-.5f:ay==1?0.f:-height,bottom=ay==0?height*.5f:ay==1?height:0.f;
    const float angle=vm.floating(0x50),cosine=float(std::cos(double(angle))),sine=float(std::sin(double(angle)));
    for(u32 i=0;i<4;++i){const float x=(i&1)?right:left,y=(i&2)?bottom:top;float outx=x*cosine-y*sine,outy=y*cosine+x*sine;outx+=center[0];outy+=center[1];AnmView v{quad.vertices[i].data()};v.put(0,word(outx));v.put(4,word(outy));v.put(8,word(center[2]));}return 0;
}
i32 draw_anm_billboard(u32 manager,u32 current,AnmView vm,AnmView camera,AnmQuad& quad,bool fog,u32 physical_width,u32 physical_height,AnmRenderMemory& memory,AnmSpriteDevice& device){
    const i32 built=build_anm_billboard(vm,camera,quad);if(built)return built;
    if(!fog)return submit_anm_quad(manager,current,vm,camera,quad,0,memory,device)?0:-2;
    StageVector delta;for(u32 i=0;i<3;++i){delta[i]=vm.floating(0x59c+i*4)+vm.floating(0x3c+i*4);delta[i]+=vm.floating(0x4ec+i*4);delta[i]-=camera.floating(i*4);}
    if((vm.get(0x1c)&0x60000)&&!vm.get(0x594)){delta[0]+=float(i32(physical_width))*.5f;float y=float(i32(physical_height))-448.f;y*=.5f;delta[1]+=y;}
    float squared=delta[1]*delta[1]+delta[0]*delta[0];squared+=delta[2]*delta[2];const float distance=float(std::sqrt(double(squared))),near=camera.floating(0x110),span=near-camera.floating(0x114);
    u32 enabled,factor;if(!memory.read_render_memory(manager+0xff75a8,&enabled,4)||!memory.read_render_memory(manager+0xff75a4,&factor,4))return -2;
    const u32 mode=(vm.get(0x18)>>17)&3;u32 primary=vm.get(0x534),secondary=vm.get(0x538);if(mode==1)primary=secondary;if(enabled){primary=tint(primary,factor);secondary=tint(secondary,factor);}
    if(distance>near){const float weight=(near-distance)/span;if(weight>=1.f)return -1;primary=fade_color(primary,camera,weight,mode<2);if(mode>=2)secondary=fade_color(secondary,camera,weight,false);}
    for(u32 i=0;i<4;++i){u32 color=primary;if(mode==2&&(i&1))color=secondary;if(mode==3&&(i&2))color=secondary;AnmView{quad.vertices[i].data()}.put(16,color);}
    return submit_anm_quad(manager,current,vm,camera,quad,2,memory,device)?0:-2;
}
}
