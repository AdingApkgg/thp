#include "BulletRectangleCancel.hpp"
#include <cmath>
namespace th143 {
namespace {
bool overlap(float x,float y,float width,float height,float radius){
 const float half_width=width*.5f,half_height=height*.5f;
 if(half_width+radius>=std::fabs(x)&&half_height>=std::fabs(y))return true;
 if(half_width>=std::fabs(x)&&half_height+radius>=std::fabs(y))return true;
 const float a=x-half_width,b=y-half_height,r=radius*radius;
 if(r>a*a+b*b)return true;const float c=x+half_width;if(r>c*c+b*b)return true;
 const float d=y+half_height;return r>a*a+d*d||r>c*c+d*d;
}
}
bool cancel_bullets_rectangle(u32 manager,const std::array<float,3>& p,const std::array<float,3>& size,float angle,i32 kind,const float& elapsed,BulletCancelGlobals& g,AnmWorld& world,BulletRectangleCancelHost& host){
 if(!host.cancel_write(manager+0x44,p.data(),12)||!host.cancel_write(manager+0x50,size.data(),12))return false;
 const float sine=float(std::sin(double(-angle))),cosine=float(std::cos(double(-angle)));
 const float clip_sine=float(std::sin(-0.)),clip_cosine=float(std::cos(-0.));
 for(u32 i=0;i<2000;++i){const u32 token=manager+0x8c+i*0x13f4;u32 word_state;if(!host.cancel_read(token+0xc0c,&word_state,4))return false;const u32 state=word_state>>16;if(state!=1&&state!=2)continue;
  BulletView b{nullptr};if(!host.cancel_bullet_view(token,b)||!b.data)return false;if(b.get(0x24))continue;
  const float radius=b.floating(0x13bc)*b.floating(0xbe0),dx=b.floating(0xbc0)-p[0],dy=b.floating(0xbc4)-p[1];
  const float x=cosine*dx-sine*dy,y=cosine*dy+sine*dx;if(!overlap(x,y,size[0],size[1],radius))continue;
  const float cx=b.floating(0xbc0)-0.f,cy=b.floating(0xbc4)-224.f;
  if(!overlap(clip_cosine*cx-clip_sine*cy,clip_cosine*cy+clip_sine*cx,384.f,448.f,radius))continue;
  u32 resource;if(!host.cancel_read(manager+0x9bf6cc,&resource,4)||!cancel_bullet(b,kind,resource,elapsed,g,world,host))return false;
 }
 return host.cancel_enemy_rectangle(p,size,angle,kind);
}
}
