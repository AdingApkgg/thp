#include "AnmQuad.hpp"
namespace th143 {
bool anm_quad_position(AnmView vm,const AnmViewport& viewport,AnmTransformHost& host,AnmQuad& out){
    static constexpr float xs[4][4]={{-.5f,.5f,-.5f,.5f},{0,1,0,1},{-1,0,-1,0},{-.5f,-.5f,.5f,.5f}};
    static constexpr float ys[4][4]={{-.5f,-.5f,.5f,.5f},{0,0,1,1},{-1,-1,0,0},{1,0,0,0}};
    if(!vm.data)return false;const u32 flags=vm.get(0x18),flags2=vm.get(0x1c),ax=(flags>>21)&3,ay=(flags>>23)&3,mode=(flags2>>19)&7;
    float sx=vm.floating(0x68)*vm.floating(0x60),sy=vm.floating(0x6c)*vm.floating(0x64);
    if(vm.get(0x594)&&!(flags2&0x8000)){auto parent=host.transform_parent(vm.get(0x594));if(!parent.data)return false;const float px=parent.floating(0x68)*parent.floating(0x60),py=parent.floating(0x6c)*parent.floating(0x64);sx=px*sx;sy=py*sy;}
    std::array<float,3> position;if(!anm_position(vm,viewport,host,position))return false;
    float z=vm.floating(0x5a4)+vm.floating(0x44);z+=vm.floating(0x4f4);
    for(u32 i=0;i<4;++i){float x=xs[ax][i]*vm.floating(0x80),y=vm.floating(0x84)*ys[ay][i];x-=vm.floating(0x90);y-=vm.floating(0x94);
        if(mode==1){x*=viewport.scale;y*=viewport.scale;}else if(mode==2){const float scale=viewport.scale*.5f;x=scale*x;y=scale*y;}
        x*=sx;y*=sy;x+=position[0];y+=position[1];AnmView v{out.vertices[i].data()};v.put(0,word(x));v.put(4,word(y));v.put(8,word(z));
    }return true;
}
}
