#include "AchievementUnlockNov14.hpp"
namespace th143 {
bool unlock_achievement(AnmView save,u32 id,AchievementUnlockHost& h,u32& result){
 if(!save.data||id>=70)return false;
 if(save.data[0xeff9+id]){result=0;return true;}
 save.data[0xeff9+id]=1;u32 queue=0;
 if(!h.achievement_read(0x4e6bc4,&queue,4))return false;
 if(queue){u32 count,capacity;
  if(!h.achievement_read(queue+0x214,&count,4)||!h.achievement_read(queue+0x218,&capacity,4))return false;
  if(signed_word(count)<signed_word(capacity)){
   if(!h.achievement_write(queue+0x14+count*4,&id,4))return false;
   ++count;if(!h.achievement_write(queue+0x214,&count,4))return false;
  }result=queue;return true;
 }
 const u32 bytes=0x248;u32 allocated=0,created=0;
 if(!h.achievement_call(0x48a697,0,&bytes,1,allocated))return false;
 if(allocated&&!h.achievement_call(0x4678e0,allocated,nullptr,0,created))return false;
 u32 failed=0;if(!h.achievement_call(0x467940,created,&id,1,failed))return false;
 if(!failed){result=created;return true;}
 if(created){u32 ignored;
  if(!h.achievement_call(0x467a30,created,nullptr,0,ignored)||!h.achievement_call(0x48a6e8,0,&created,1,ignored))return false;
 }result=0;return true;
}
}
