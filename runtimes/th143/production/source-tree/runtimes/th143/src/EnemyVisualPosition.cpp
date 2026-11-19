#include "EnemyVisualPosition.hpp"
#include <cmath>
#include <array>
namespace th143 {
bool position_enemy_animation(AnmView a,u32 slot,AnmView target,AnmView parent,bool direct,float rate){
 if(slot>=22)return false;
 if(!target.data){if(!direct)a.put(0x124+slot*4,0);return true;}
 std::array<float,3> p;
 if(direct)for(u32 i=0;i<3;++i)p[i]=a.floating(0x44+i*4);
 else{
  p={a.floating(0x184+slot*12)+a.floating(0x44),a.floating(0x188+slot*12)+a.floating(0x48),a.floating(0x4c)+a.floating(0x18c+slot*12)};
  if(signed_word(a.get(0x2a4+slot*4))>=0){if(!parent.data)return false;for(u32 i=0;i<3;++i)p[i]=parent.floating(0x3c+i*4)+p[i];}
 }
 for(u32 i=0;i<3;++i)target.put(0x59c+i*4,word(p[i]));
 if(!direct&&(target.get(0x1c)&0x40)&&rate>real(0x3b03126f)){
  const float angle=float(std::atan2(double(a.floating(0x7c)),double(a.floating(0x78))));target.put(0x18,target.get(0x18)|4);target.put(0x50,word(angle));a.put(0x120,word(angle));
 }return true;
}
}
