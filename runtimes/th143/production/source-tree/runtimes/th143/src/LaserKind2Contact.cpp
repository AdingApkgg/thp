#include "LaserKind2Contact.hpp"
#include "DirectionVector.hpp"
namespace th143 {
bool contact_laser_kind2(AnmView v,u32 token,bool forced,u32& caller_z_scratch,LaserKind2ContactHost& host){
 const u32 points=v.get(0x14ac);float distance=0.f;bool grazed=false;std::array<float,3> graze{};
 for(i32 i=0;i+1<signed_word(v.get(0x5e0));++i){
  if(i>=4096)return false;std::array<u8,32> bytes;if(!host.laser_contact_read(points+u32(i)*32,bytes.data(),32))return false;AnmView p{bytes.data()};
  const float speed=p.floating(0x1c),angle=p.floating(0x18);DirectionVector direction;if(!direction_vector(angle,speed*.5f,direction))return false;
  const std::array<float,3> center{p.floating(0)+direction.x,p.floating(4)+direction.y,p.floating(8)+real(caller_z_scratch)};caller_z_scratch=word(center[2]);distance+=speed;
  if(distance<16.f)continue;const float width=v.floating(0x74);const float contact_width=width<=32.f?width*.5f:(width-32.f)*real(0x3e99999a)+16.f;
  i32 result;if(!host.laser_player_rectangle(center,speed,contact_width,angle,forced,result))return false;
  if(result==1){std::array<float,3> player;if(!host.laser_player_position(player)||!host.laser_player_cancel(token,player,{32.f,32.f,0.f},0.f,0,true))return false;}
  else if(result==2&&!grazed&&signed_word(v.get(0x30))%3==0){graze=center;grazed=true;}
 }
 if(grazed&&!host.laser_player_graze(graze))return false;
 const u32 previous=v.get(0x30),pointer=v.get(0x38);float rate=1.f;if(pointer&&!host.timer_rate(pointer,rate))return false;const bool unit=!pointer||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));
 const float next=v.floating(0x34)+(unit?1.f:rate);const u32 count=unit?previous+1:next>=-2147483648.f&&next<2147483648.f?u32(i32(next)):0x80000000;
 v.put(0x2c,previous);v.put(0x34,word(next));v.put(0x30,count);return true;
}
}
