#include "LaserKind0Contact.hpp"
#include "LaserCircleInterval.hpp"
#include "DirectionVector.hpp"
#include <cmath>
namespace th143 {
bool contact_laser_kind0(AnmView v,u32 token,bool forced,LaserKind0ContactHost& host){
 if(!v.data)return false;const float length=v.floating(0x70),width=v.floating(0x74);if(!(length>16.f)||!(width>3.f))return true;
 const float angle=v.floating(0x6c);DirectionVector direction;if(!direction_vector(angle,length/10.f,direction))return false;
 const std::array<float,3> origin{v.floating(0x54)+direction.x,v.floating(0x58)+direction.y,v.floating(0x5c)+0.f};
 const float contact_width=width<32.f?width*.5f:width-(width+16.f)*.5f,contact_length=(length*4.f)/5.f;
 i32 result;if(!host.laser_player_rectangle(origin,contact_length,contact_width,angle,forced,result))return false;
 if(result==1){std::array<float,3> player;if(!host.laser_player_position(player))return false;return host.laser_player_cancel(token,player,{32.f,32.f,0.f},0.f,0,true);}
 if(result!=2)return true;
 if(signed_word(v.get(0x30))%3==0){
  std::array<float,3> player;if(!host.laser_player_position(player))return false;float begin=0,end=0;bool intersects;
  if(!laser_circle_interval(origin,player,angle,32.f,begin,end,intersects))return false;
  if(intersects){if(!direction_vector(angle,begin,direction))return false;player={origin[0]+direction.x,origin[1]+direction.y,origin[2]+0.f};}
  if(!host.laser_player_graze(player))return false;
 }
 const u32 previous=v.get(0x30),pointer=v.get(0x38);float rate=1;if(pointer&&!host.timer_rate(pointer,rate))return false;
 const bool unit=!pointer||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float next=v.floating(0x34)+(unit?1.f:rate);if(!std::isfinite(next))return false;
 v.put(0x2c,previous);v.put(0x34,word(next));v.put(0x30,unit?previous+1:next>=-2147483648.f&&next<2147483648.f?u32(i32(next)):0x80000000u);return true;
}
}
