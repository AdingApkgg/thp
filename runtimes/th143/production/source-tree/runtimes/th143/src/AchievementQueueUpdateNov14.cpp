#include "AchievementQueueUpdateNov14.hpp"
#include <cstring>
namespace th143 {
bool update_achievement_queue(AnmView q,u32 self,AchievementQueueUpdateHost& h,u32& result){
 if(!q.data)return false;const u32 phase=q.get(0x220);
 if(phase==2){if(!h.achievement_destroy(self))return false;result=1;return true;}
 if(phase==0&&q.get(0x214)){
  const u32 count=q.get(0x214);if(signed_word(count)<0||count>128)return false;
  const u32 id=q.get(0x14);q.put(0x214,count-1);std::memmove(q.data+0x14,q.data+0x18,127*4);
  change_achievement_phase(q,1);
  for(u32 i=0;i<3;++i){u32 handle;if(!h.achievement_spawn(q.get(0x10),i?i+3:0,handle))return false;q.put(0x23c+i*4,handle);}
  u32 vm,text;if(!h.achievement_find(q.get(0x240),vm))return false;if(!vm)q.put(0x240,0);
  if(!h.achievement_name(id,text)||!h.achievement_text(vm,0x4c7f84,text,true))return false;
  if(!h.achievement_find(q.get(0x244),vm))return false;if(!vm)q.put(0x244,0);
  if(!h.achievement_text(vm,0x4c7f70,0,false)||!h.achievement_sound(86))return false;
 }
 if((phase==0||phase==1)&&signed_word(q.get(0x22c))>=180)change_achievement_phase(q,q.get(0x214)?0:2);
 const u32 old=q.get(0x22c),token=q.get(0x234);q.put(0x228,old);float rate=1;
 if(token&&!h.achievement_rate(token,rate))return false;
 const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));
 const float value=q.floating(0x230)+(unit?1.f:rate);q.put(0x230,word(value));
 q.put(0x22c,unit?old+1:(value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000));
 result=1;return true;
}
}
