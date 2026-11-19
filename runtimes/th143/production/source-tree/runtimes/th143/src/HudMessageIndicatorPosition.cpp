#include "HudMessageIndicatorPosition.hpp"
namespace th143 {
bool update_hud_message_indicator_position(AnmView s,float viewport_scale,HudMessageTextCallbackHost& host){
 auto root=host.message_callback_visual(s.get(0x6c));if(!root.data){s.put(0x6c,0);return false;}
 auto child=host.message_callback_child(root,signed_word(s.get(0x1b4)+0x9f));if(!child.data)return true;
 std::array<float,3> p;
 p[0]=child.floating(0x59c)+child.floating(0x3c);p[0]+=child.floating(0x4ec);
 p[1]=child.floating(0x40)+child.floating(0x5a0);p[1]=child.floating(0x4f0)+p[1];
 p[2]=child.floating(0x44)+child.floating(0x5a4);p[2]=child.floating(0x4f4)+p[2];
 if(!host.message_callback_transform(child,p))return false;
 const float scale=2.f/viewport_scale;p[0]*=scale;p[1]*=scale;
 if(signed_word(s.get(0x190))>=1){const float t=child.floating(0x60);if(1.f>t){float x=t+.125f;x*=32.f;x-=6.f;p[0]=x+p[0];}else p[0]+=26.f;}else p[0]-=36.f;
 for(u32 at:{0x58u,0x60u,0x5cu,0x64u}){auto v=host.message_callback_visual(s.get(at));if(v.data)for(u32 i=0;i<3;++i)v.put(0x59c+i*4,word(p[i]));}return true;
}
}
