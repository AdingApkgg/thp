#include "LaserKind0BounceUpdate.hpp"
#include "LaserKind0LinearMotion.hpp"
#include "LaserKind0Bounds.hpp"
#include <cmath>
namespace th143 {
bool update_laser_kind0_with_bounce(AnmView v,u32 token,LaserKind0OrdinaryHost& host,LaserKind0BounceServices& bounce,i32& result){
 if(!v.data)return false;
 for(u32 iterations=0;;++iterations){
  if(iterations>=64||!dispatch_laser_kind0_bounce(v,bounce))return false;
  const u32 active=v.get(0x598);if(active&~0x40u)return false;if(!active)break;
  i32 completed=0;if((active&0x40)&&!advance_laser_kind0_bounce(v,bounce,completed))return false;
  if(v.get(0x5b4))v.put(0x5b4,v.get(0x5b4)-1);
  if(!completed)break;
 }
 float rate;if(!host.timer_rate(host.global_rate_token(),rate))return false;
 bool expired;if(!advance_laser_kind0_linear(v,rate,expired))return false;if(expired){result=1;return true;}
 if(!laser_kind0_bounds(v,host,expired))return false;if(expired){result=1;return true;}
 if(!host.laser_kind0_contact(token,0))return false;
 u32 width,height;const u32 sprite=v.get(0x940);if(!sprite||!host.read(sprite+0x38,&height,4)||!host.read(sprite+0x34,&width,4))return false;
 AnmView main=v.sub(0x914);main.put(0x60,word(v.floating(0x74)/real(height)));main.put(0x18,main.get(0x18)|8);main.put(0x64,word(v.floating(0x70)/real(width)));main.put(0x18,main.get(0x18)|8);
 if(anm_step(main,host)==-2)return false;
 if(v.floating(0x7c)==0.f&&anm_step(v.sub(0xee0),host)==-2)return false;
 if(anm_step(v.sub(0x14ac),host)==-2)return false;
 const u32 previous=v.get(0x44),pointer=v.get(0x4c);float elapsed=1;if(pointer&&!host.timer_rate(pointer,elapsed))return false;
 const bool unit=!pointer||(elapsed>real(0x3f7d70a4)&&elapsed<real(0x3f8147ae));const float next=v.floating(0x48)+(unit?1.f:elapsed);if(!std::isfinite(next))return false;
 v.put(0x40,previous);v.put(0x48,word(next));v.put(0x44,unit?previous+1:next>=-2147483648.f&&next<2147483648.f?u32(i32(next)):0x80000000u);result=0;return true;
}
}
