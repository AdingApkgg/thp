#include "LaserKind0Bounds.hpp"
#include "DirectionVector.hpp"
#include <cmath>
namespace th143 {
bool laser_kind0_bounds(AnmView v,AnmTimerHost& host,bool& expired){
 if(!v.data)return false;expired=false;
 if(signed_word(v.get(0x5a4))>0){
  float rate=1.f;const u32 pointer=v.get(0x5ac);if(pointer&&!host.timer_rate(pointer,rate))return false;
  const bool unit=!pointer||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));
  const float next=v.floating(0x5a8)-(unit?1.f:rate);if(!std::isfinite(next))return false;
  v.put(0x5a0,v.get(0x5a4));v.put(0x5a8,word(next));v.put(0x5a4,next>=-2147483648.f&&next<2147483648.f?u32(i32(next)):0x80000000u);return true;
 }
 const float x=v.floating(0x54),y=v.floating(0x58),width=v.floating(0x74);
 if(!std::isfinite(x)||!std::isfinite(y)||!std::isfinite(width))return false;
 DirectionVector direction;if(!direction_vector(v.floating(0x6c),v.floating(0x70),direction))return false;
 auto inside=[&](float px,float py){return px+width>-192.f&&px-width<192.f&&py+width>0.f&&py-width<448.f;};
 expired=!inside(x,y)&&!inside(x+direction.x,y+direction.y);return true;
}
}
