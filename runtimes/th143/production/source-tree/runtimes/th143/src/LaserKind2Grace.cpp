#include "LaserKind2Grace.hpp"
namespace th143 {
bool activate_laser_kind2_grace(AnmView v,u32 rate){
 const i32 cursor=signed_word(v.get(0x594));if(cursor>=18)return true;if(cursor<0)return false;
 const u32 row=0x5ec+u32(cursor)*0x2c,type=v.get(row+0x20),flags=v.get(0x598);
 if(!type||(!(v.get(row+0x24))&&flags)||(type&flags))return true;if(type!=0x100)return false;
 v.put(0x598,flags|type);if(!(v.get(0x3ac)&1)){v.put(0x3a8,rate);v.put(0x3ac,v.get(0x3ac)|1);}
 const u32 duration=v.get(row+0x10);v.put(0x39c,duration-1);v.put(0x3a0,duration);v.put(0x3a4,word(float(signed_word(duration))));v.put(0x3d0,v.get(row+0x14));v.put(0x594,u32(cursor)+1);return true;
}
bool update_laser_kind2_grace(AnmView v,AnmTimerHost& host,i32& result){
 const u32 token=v.get(0x3a8);float rate=1.f;if(token&&!host.timer_rate(token,rate))return false;
 v.put(0x39c,v.get(0x3a0));const bool unit=!token||(rate>real(0x3f7d70a4)&&real(0x3f8147ae)>rate);
 const float fraction=v.floating(0x3a4)-(unit?1.f:rate*1.f);const u32 count=fraction>=-2147483648.f&&fraction<2147483648.f?u32(i32(fraction)):0x80000000;
 v.put(0x3a4,word(fraction));v.put(0x3a0,count);result=0;if(signed_word(count)<=0){v.put(0x598,v.get(0x598)^0x100u);result=1;}return true;
}
}
