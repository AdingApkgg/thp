#include "AnmGeometry.hpp"
#include "DirectionVector.hpp"

namespace th143 {
namespace {
float wrap(float value){
    u32 count=0;const float tau=real(0x40c90fdb);
    while(value>real(0x40490fdb)){value-=tau;if(count++>32)break;}
    while(real(0xc0490fdb)>value){value+=tau;if(count++>32)break;}
    return value;
}
void put(std::vector<u8>& b,u32 at,u32 value){std::memcpy(b.data()+at,&value,4);}
void fp(std::vector<u8>& b,u32 at,float value){put(b,at,word(value));}
bool polar(std::vector<u8>& b,u32 at,float angle,float radius){
    DirectionVector v;if(!direction_vector(angle,radius,v))return false;fp(b,at,v.x);fp(b,at+4,v.y);return true;
}
bool transformed_vertex(std::vector<u8>& b,u32 at,float angle,float radius,u32 color,float u,float v,const std::array<float,3>& origin){
    put(b,at+12,word(1.f));put(b,at+16,color);fp(b,at+20,u);fp(b,at+24,v);
    if(!polar(b,at,angle,radius))return false;put(b,at+8,0);
    AnmView point{b.data()+at};for(u32 i=0;i<3;++i)fp(b,at+i*4,point.floating(i*4)+origin[i]);return true;
}
}
bool anm_geometry(AnmView s,std::vector<u8>& b,const AnmGeometryContext& context){
    const u32 mode=(s.get(0x18)>>25)&31;
    if(mode!=9&&mode!=13&&mode!=14&&mode!=24&&mode!=25)return true;
    const i32 count=signed_word(s.get(0x4ac));if(count<1||count>65536)return false;
    const u32 stride=mode<24?56:48;if(b.size()<std::uint64_t(count)*stride)return false;
    const float denominator=float(count-1),v_step=float(signed_word(s.get(0x4b0)))/denominator;
    const u32 color=(s.get(0x18)&0x60000)?s.get(0x538):s.get(0x534);
    float progress=0;
    if(mode==24||mode==25){
        const float arc=s.floating(0x4bc),step=arc/denominator,half=s.floating(0x4c0)*.5f,radius=s.floating(0x4c4);
        float angle=wrap(s.floating(0x4c8)-arc*.5f),first_radius=radius,second_radius=radius,first_y=half;
        if(mode==25){first_radius=radius-half;second_radius=half+radius;first_y=0;}
        const float second_y=real(word(first_y)^0x80000000u);
        for(i32 i=0;i<count;++i){
            const u32 at=u32(i)*48;DirectionVector first,second;
            if(!direction_vector(angle,first_radius,first)||!direction_vector(angle,second_radius,second))return false;
            fp(b,at,first.x);fp(b,at+4,first_y);fp(b,at+8,first.y);put(b,at+12,color);fp(b,at+16,s.floating(0x88)+s.floating(0x3b8));fp(b,at+20,s.floating(0x8c)+progress);
            fp(b,at+24,second.x);fp(b,at+28,second_y);fp(b,at+32,second.y);put(b,at+36,color);fp(b,at+40,s.floating(0x3c0)+s.floating(0x88));fp(b,at+44,s.floating(0x8c)+progress);
            progress+=v_step;angle=wrap(angle+step);
        }return true;
    }
    const float half=s.floating(0x60)*.5f;float outer=s.floating(0x64)+half,inner=s.floating(0x64)-half;
    if(s.get(0x594)&&!(s.get(0x1c)&0x8000)){outer*=context.parent_scale[0];inner=context.parent_scale[1]*inner;}
    const u32 scaling=(s.get(0x1c)>>19)&7;
    if(scaling==1||scaling==2){const float scale=scaling==2?context.viewport_scale*.5f:context.viewport_scale;outer*=scale;inner=scale*inner;}
    const float step=(mode==9?real(0x40c90fdb):s.floating(0x48))/denominator;
    float angle=mode==9?s.floating(0x50):wrap(s.floating(0x50)-s.floating(0x48)*.5f);
    if(mode==14)angle=wrap(s.floating(0x50));
    const i32 iterations=mode==9?count-1:count;
    for(i32 i=0;i<iterations;++i){
        const u32 at=u32(i)*56;const float v=s.floating(0x8c)+progress;
        if(!transformed_vertex(b,at,angle,outer,mode==9?s.get(0x534):color,s.floating(0x88)+s.floating(0x3b8),v,context.position)||
           !transformed_vertex(b,at+28,angle,inner,color,s.floating(0x3c0)+s.floating(0x88),v,context.position))return false;
        progress+=v_step;angle=wrap(angle+step);
    }
    if(mode==9){const u32 at=u32(count-1)*56;if(at)std::memcpy(b.data()+at,b.data(),56);fp(b,at+24,s.floating(0x8c)+progress);fp(b,at+52,s.floating(0x8c)+progress);}
    return true;
}
}
