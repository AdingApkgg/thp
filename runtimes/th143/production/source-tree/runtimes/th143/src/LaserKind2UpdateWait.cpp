#include "LaserKind2Wait.hpp"
#include "LaserKind2CartesianPath.hpp"
#include "LaserKind2Update.hpp"
namespace th143 {
namespace {
u32 truncate(float f){return f>=-2147483648.f&&f<2147483648.f?u32(i32(f)):0x80000000u;}
bool rate_for(AnmView v,u32 at,AnmTimerHost& host,float& rate,bool& unit){
 const u32 pointer=v.get(at);rate=1.f;if(pointer&&!host.timer_rate(pointer,rate))return false;
 unit=!pointer||(rate>real(0x3f7d70a4)&&real(0x3f8147ae)>rate);return true;
}
bool decrement(AnmView v,u32 at,AnmTimerHost& host){
 float rate;bool unit;if(!rate_for(v,at+12,host,rate,unit))return false;
 v.put(at,v.get(at+4));const float next=v.floating(at+8)-(unit?1.f:rate*1.f);
 v.put(at+8,word(next));v.put(at+4,truncate(next));return true;
}
bool dispatch(AnmView v,u32 token,LaserKind2UpdateHost& host){
 for(u32 steps=0;steps<19;++steps){
  const i32 cursor=signed_word(v.get(0x594));if(cursor>=18)return true;if(cursor<0)return false;
  const u32 row=0x5ec+u32(cursor)*0x2c,type=v.get(row+0x20),active=v.get(0x598);
  if(!type||(!v.get(row+0x24)&&active)||(type&active))return true;
  if(type==0x100){if(!activate_laser_kind2_grace(v,host.global_rate_token()))return false;}
  else if(type==0x80000000u){if(!activate_laser_kind2_wait(v,host.global_rate_token()))return false;}
  else if(type==4){if(!activate_laser_kind2_cartesian_path(v,token,host))return false;}
  else if(type==8){if(!activate_laser_kind2_polar_path(v,token,host))return false;}
  else return false;
 }
 return false;
}
}
bool update_laser_kind2(AnmView v,u32 token,LaserKind2UpdateHost& host,i32& result){
 if(!v.data)return false;
 for(u32 steps=0;;++steps){
  if(steps>=64||!dispatch(v,token,host))return false;
  const u32 active=v.get(0x598);if(!active)break;if(active&~0x80000100u)return false;
  i32 completed=0;
  if(active&0x100u){i32 value;if(!update_laser_kind2_grace(v,host,value))return false;completed+=value;}
  if(v.get(0x598)&0x80000000u){
   if(signed_word(v.get(0x1f0))<=0){v.put(0x598,v.get(0x598)^0x80000000u);++completed;}
   else if(!decrement(v,0x1ec,host))return false;
  }
  const u32 delay=v.get(0x5b4);if(delay)v.put(0x5b4,delay-1);
  if(!completed)break;
 }
 if(!refresh_laser_kind2_points(v,token,host))return false;
 if(signed_word(v.get(0x5a4))>0||(v.get(0x598)&0x100u)){
  if(!decrement(v,0x5a0,host))return false;
 }else{
  bool inside=false;const i32 count=signed_word(v.get(0x5e0));const float width=v.floating(0x74);
  if(count>4096)return false;
  for(i32 i=0;i<count;++i){
   std::array<u32,2> point;if(!host.laser_point_read(v.get(0x14ac)+u32(i)*32,point.data(),8))return false;
   const float x=real(point[0]),y=real(point[1]);
   if(-192.f>=x+width||x-width>=192.f||0.f>=y+width)continue;
   // COMISS/JB accepts unordered values in the final upper-Y comparison.
   if(!(y-width>=448.f)){inside=true;break;}
  }
  if(!inside){result=1;return true;}
 }
 if(!host.laser_kind2_update_contact(token,false)||!host.laser_kind2_update_animation(token+0x914,v.sub(0x914))||!host.laser_kind2_update_animation(token+0xee0,v.sub(0xee0)))return false;
 const u32 previous=v.get(0x44);float rate;bool unit;if(!rate_for(v,0x4c,host,rate,unit))return false;
 const float next=v.floating(0x48)+(unit?1.f:rate);v.put(0x40,previous);v.put(0x48,word(next));v.put(0x44,unit?previous+1:truncate(next));result=0;return true;
}
}
