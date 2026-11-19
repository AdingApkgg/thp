#include "AchievementQueueLifecycleNov14.hpp"
#include <cstring>
#include <initializer_list>
namespace th143 {
void change_achievement_phase(AnmView q,u32 phase){
 q.put(0x21c,q.get(0x220));q.put(0x220,phase);q.put(0x224,0);
 if(!(q.get(0x238)&1)){q.put(0x234,0x4e40b0);q.put(0x238,q.get(0x238)|1);}
 q.put(0x22c,0);q.put(0x230,0);q.put(0x228,0xffffffff);
}
bool construct_achievement_queue(AnmView q,u32 self,AchievementUnlockHost& h){
 if(!q.data)return false;
 std::memset(q.data,0,0x248);q.put(0,2);
 if(!h.achievement_write(0x4e6bc4,&self,4))return false;
 change_achievement_phase(q,0);q.put(0x218,60);return true;
}
bool start_achievement_queue(AnmView q,u32 self,u32 id,AchievementUnlockHost& h,u32& result){
 if(!q.data)return false;u32 returned;
 auto call=[&](u32 e,u32 owner,std::initializer_list<u32> args){return h.achievement_call(e,owner,args.begin(),u32(args.size()),returned);};
 auto put=[&](u32 p,u32 value){return h.achievement_write(p,&value,4);};
 auto read=[&](u32 p,u32& value){return h.achievement_read(p,&value,4);};
 if(!call(0x482140,0,{27,0x4c7f20}))return false;q.put(0x10,returned);
 if(!returned){if(!call(0x403400,0,{0x4e20a8,0x4c52bc}))return false;result=0xffffffff;return true;}
 if(!call(0x401830,0,{0x468100}))return false;const u32 update=returned;u32 flags;
 if(!read(update+4,flags)||!put(update+4,flags|2)||!put(update+0x24,self)||!call(0x4013e0,0,{update,13}))return false;q.put(8,update);
 if(!call(0x48a697,0,{40}))return false;const u32 draw=returned;if(!draw)return false;
 if(!read(draw+4,flags)||!put(draw+4,flags|3))return false;
 for(u32 at:{0u,12u,16u,24u,28u,32u})if(!put(draw+at,0))return false;
 if(!put(draw+8,0x468110)||!put(draw+20,draw)||!put(draw+36,self)||!call(0x401490,0,{draw,70}))return false;q.put(12,draw);
 const u32 count=q.get(0x214);if(signed_word(count)<signed_word(q.get(0x218))){if(count>=128)return false;q.put(0x14+count*4,id);q.put(0x214,count+1);}
 change_achievement_phase(q,0);result=0;return true;
}
bool destroy_achievement_queue(AnmView q,AchievementUnlockHost& h){
 if(!q.data)return false;
 auto read=[&](u32 p,u32& value){return h.achievement_read(p,&value,4);};
 auto put=[&](u32 p,u32 value){return h.achievement_write(p,&value,4);};
 u8 threaded;if(!h.achievement_read(0x538f4e,&threaded,1)||threaded)return false;
 u32 scheduler;if(!read(0x4e69f4,scheduler))return false;
 for(u32 at:{8u,12u}){
  if(at==12&&!read(0x4e69f4,scheduler))return false;
  const u32 token=q.get(at);if(token){u32 ignored;if(!h.achievement_call(0x4018f0,scheduler,&token,1,ignored))return false;}
 }
 u32 pool;if(!read(0x538de8,pool))return false;
 for(u32 at:{0xfe8218u,0xfe8220u}){
  u32 node;if(!read(pool+at,node))return false;
  while(node){u32 actor,next,resource,flags;
   if(!read(node,actor)||!read(node+4,next)||!read(actor+0x30,resource))return false;
   if(resource==q.get(0x10)){if(!read(actor+0x1c,flags)||!put(actor+0x1c,flags|0x20))return false;}
   node=next;
  }
 }return put(0x4e6bc4,0);
}
}
