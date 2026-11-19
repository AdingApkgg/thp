#include "BulletOffscreenGrace.hpp"
namespace th143 {
void start_bullet_offscreen_grace(BulletView b,u32 row,u32 rate){
 b.put(0xc04,b.get(0xc04)|0x100);
 if(!(b.get(0x1268)&1)){b.put(0x1264,rate);b.put(0x1268,b.get(0x1268)|1);}
 const u32 duration=b.get(row+0x10);
 b.put(0x1258,duration-1);b.put(0x125c,duration);b.put(0x1260,word(float(signed_word(duration))));
 b.put(0x128c,b.get(row+0x14));
}
i32 update_bullet_offscreen_grace(BulletView b,BulletMotionHost& host){
 if(b.get(0x128c))return -2;
 float rate=1.f;const u32 token=b.get(0x1264);
 if(token&&!host.timer_rate(token,rate))return -2;
 b.put(0x1258,b.get(0x125c));
 const bool unit=!token||(rate>real(0x3f7d70a4)&&real(0x3f8147ae)>rate);
 const float fraction=b.floating(0x1260)-(unit?1.f:rate*1.f);
 const u32 value=fraction>=-2147483648.f&&fraction<2147483648.f?u32(i32(fraction)):0x80000000;
 b.put(0x1260,word(fraction));b.put(0x125c,value);
 if(signed_word(value)<=0){b.put(0xc04,b.get(0xc04)^0x100);return 1;}
 return 0;
}
}
