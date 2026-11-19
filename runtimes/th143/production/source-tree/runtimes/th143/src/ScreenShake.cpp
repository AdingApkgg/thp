#include "ScreenShake.hpp"
namespace th143 {
i32 step_screen_shake(AnmView s,ScreenShakeGlobals& g,AnmTimerHost& host){
 if(g.paused)return 7;
 const u32 token=s.get(0x3c),previous=s.get(0x34);float rate=1.f;if(token&&!host.timer_rate(token,rate))return -2;
 const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));
 s.put(0x30,previous);const float elapsed=s.floating(0x38)+(unit?1.f:rate);
 const u32 current=unit?previous+1:elapsed>=-2147483648.f&&elapsed<2147483648.f?u32(i32(elapsed)):0x80000000;
 s.put(0x34,current);s.put(0x38,word(elapsed));
 const i32 duration=signed_word(s.get(0x1c));if(signed_word(current)>=duration)return 7;
 const float difference=float(signed_word(s.get(0x24)-s.get(0x20))),progress=difference*elapsed;
 const float amplitude=progress/float(duration)+float(signed_word(s.get(0x20)));
 const u32 x=g.random.next32()%3,y=g.random.next32()%3;
 g.offsets[0]=x==0?0:x==1?word(amplitude):word(amplitude)^0x80000000u;
 const float scaled=real(g.scale)*amplitude;
 // Original471713 negates logical X but leaves scaled X positive.
 g.offsets[2]=x==0?0:word(scaled);
 g.offsets[1]=y==0?0:y==1?word(amplitude):word(amplitude)^0x80000000u;
 g.offsets[3]=y==0?0:y==1?word(scaled):word(scaled)^0x80000000u;
 return 1;
}
}
