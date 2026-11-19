#include "TitleQuitControl.hpp"
namespace th143 {
bool advance_title_quit_control(AnmView t,TitleQuitControlHost& h,u32& result){
 if(!t.data||(t.get(0xe000)&1))return false;const u32 state=t.get(0x1c);if(state!=2&&state!=8&&state!=10)return false;
 u32 flags;if(state==2){if(!h.title_quit_read(0x4e4ef4,flags)||!h.title_quit_write(0x4e4ebc,((~(flags>>13))&1)|2))return false;}
 if(!h.title_quit_read(0x4e49dc,flags)||!h.title_quit_queue(0x53b1e0,flags&0x10?4:3,0,0x4c61a4))return false;
 const u32 previous=t.get(0x2b8),token=t.get(0x2c0);t.put(0x2b4,previous);float rate=1;if(token&&!h.timer_rate(token,rate))return false;
 const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float next=t.floating(0x2bc)+(unit?1.f:rate);t.put(0x2b8,unit?previous+1:next>=-2147483648.f&&next<2147483648.f?u32(i32(next)):0x80000000);t.put(0x2bc,word(next));result=1;return true;
}
}
