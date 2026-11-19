#include "BulletTimedFreeze.hpp"
namespace th143 {
void start_bullet_timed_freeze(BulletView b,u32 row,u32 rate){
 const u32 duration=b.get(row+0x10);if(signed_word(duration)<=0)return;
 b.put(0xc04,b.get(0xc04)|0x4000000);
 if(!(b.get(0x12f8)&1)){b.put(0x12f4,rate);b.put(0x12f8,b.get(0x12f8)|1);}
 b.put(0x12e8,duration-1);b.put(0x12ec,duration);b.put(0x12f0,word(float(signed_word(duration))));
}
i32 update_bullet_timed_freeze(BulletView b,BulletMotionHost& host){
 if(!(b.get(0xc04)&0x4000000))return 0;
 if(signed_word(b.get(0x12ec))<=0){b.put(0x20,b.get(0x20)&~0x200u);b.put(0xc04,b.get(0xc04)^0x4000000);return 1;}
 float rate=1.f;const u32 token=b.get(0x12f4);if(token&&!host.timer_rate(token,rate))return -2;
 b.put(0x20,b.get(0x20)|0x200);b.put(0x12e8,b.get(0x12ec));
 const bool unit=!token||(rate>real(0x3f7d70a4)&&real(0x3f8147ae)>rate);
 const float fraction=b.floating(0x12f0)-(unit?1.f:rate*1.f);
 const u32 value=fraction>=-2147483648.f&&fraction<2147483648.f?u32(i32(fraction)):0x80000000;
 b.put(0x12f0,word(fraction));b.put(0x12ec,value);return 0;
}
}
