#include "AnmTransform.hpp"
#include "DirectionVector.hpp"

namespace th143 {
bool anm_position(AnmView s,const AnmViewport& viewport,AnmTransformHost& host,std::array<float,3>& out,u32 budget){
    if(!s.data||!budget)return false;
    out[0]=s.floating(0x3c)+s.floating(0x59c);out[0]+=s.floating(0x4ec);
    out[1]=s.floating(0x40)+s.floating(0x5a0);out[1]=s.floating(0x4f0)+out[1];
    out[2]=s.floating(0x44)+s.floating(0x5a4);out[2]=s.floating(0x4f4)+out[2];
    const u32 flags=s.get(0x1c),mode=(flags>>19)&7;
    if(mode>=1&&mode<=4){const float scale=(mode==2||mode==4)?viewport.scale*.5f:viewport.scale;for(auto& f:out)f*=scale;}
    if(s.get(0x594)&&!(flags&0x8000)){
        auto parent=host.transform_parent(s.get(0x594));if(!parent.data)return false;
        if(flags&0x400000){
            DirectionVector v;if(!direction_vector(parent.floating(0x50),1.f,v))return false;
            const float x=out[0],y=out[1];out[0]=x*v.x-y*v.y;out[1]=y*v.x+x*v.y;
        }
        std::array<float,3> origin;if(!anm_position(parent,viewport,host,origin,budget-1))return false;
        for(u32 i=0;i<3;++i)out[i]+=origin[i];return true;
    }
    const u32 origin=(flags>>17)&3;
    if(origin){const auto& p=origin==1?viewport.first_origin:viewport.second_origin;out[0]+=float(p[0]);out[1]+=float(p[1]);}
    return true;
}
}
