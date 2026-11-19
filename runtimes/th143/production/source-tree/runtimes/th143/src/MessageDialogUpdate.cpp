#include "MessageDialogUpdate.hpp"
#include "MenuCursor.hpp"
namespace th143 {
namespace {
bool read_word(MessageDialogUpdateHost& h,u32 p,u32& v){return h.dialog_update_read(p,&v,4);}
bool reset(AnmView s,MessageDialogUpdateHost& h){const u32 f=s.get(0x24);if(!(f&1)){s.put(0x20,h.global_rate_token());s.put(0x24,f|1);}s.put(0x14,0xffffffff);s.put(0x18,0);s.put(0x1c,0);return true;}
bool tick(AnmView s,MessageDialogUpdateHost& h){const u32 p=s.get(0x20),old=s.get(0x18);s.put(0x14,old);float r=1;if(p&&!h.timer_rate(p,r))return false;const bool unit=!p||(r>real(0x3f7d70a4)&&r<real(0x3f8147ae));const float value=s.floating(0x1c)+(unit?1.f:r);s.put(0x18,unit?old+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);s.put(0x1c,word(value));return true;}
}
bool update_message_dialog(AnmView s,u32 self,MessageDialogUpdateHost& h,i32& result){
 result=1;std::uint64_t returned=0;
 auto call=[&](u32 e,u32 owner,std::initializer_list<u32> args){return h.dialog_update_call(e,owner,args,returned);};
 auto resource_texture=[&](u32& descriptor){return read_word(h,s.get(0x134)+0x124,descriptor);};
 bool next_page=false;
 if(s.get(0x10)==0)s.put(0x10,1);
 else if(s.get(0x10)==2){if(signed_word(s.get(0x18))>=0){s.put(0x128,1);if(!call(0x46f4e0,0,{}))return false;const auto stamp=returned;if(!h.dialog_update_write(0x4e47c4,&stamp,8))return false;}}
 else if(s.get(0x10)==1){
  const u32 sub=s.get(0x13c);
  if(sub==0){
   if(!call(0x433830,0,{}))return false;
   u32 start;if(!read_word(h,0x4c8020+s.get(0x130)*4,start))return false;s.put(0x30,99);
   if(!MenuCursor{{s.data+0x28}}.select(signed_word(start)))return false;
   s.put(0xf8,1);u32 descriptor;if(!resource_texture(descriptor)||!call(0x484a40,descriptor+0x18,{}))return false;
   s.put(0x13c,1);if(!call(0x472be0,0,{7}))return false;
   if(s.get(0x130)==8){u32 save;u8 unlocked;if(!read_word(h,0x4e6b9c,save)||!h.dialog_update_read(save+0xf08a,&unlocked,1))return false;if(!unlocked&&(!call(0x436ee0,0,{})||!call(0x436c30,0,{1})))return false;}
   next_page=true;
  }else if(sub==3){
   u32 descriptor;if(!resource_texture(descriptor)||!call(0x481990,0,{descriptor+0x18,s.get(0x138),s.get(0x1c0),1}))return false;
   if(s.get(0x138)){if(!call(0x48a7bc,0,{s.get(0x138)}))return false;s.put(0x138,0);}s.put(0x138,0);
   u32 texture;if(!resource_texture(descriptor)||!read_word(h,descriptor+0x18,texture)||!call(0x24,texture,{}))return false;
   if(!call(0x4682c0,self,{word(128.f),0,0}))return false;s.put(0x13c,4);reset(s,h);
   // The original falls through to state4 and rechecks the reset timer.
  }
  if(sub==3||sub==4){
   if(signed_word(s.get(0x18))>=20){u32 fresh;if(!read_word(h,0x4e19dc,fresh))return false;if((fresh&0x80001)&&signed_word(s.get(0x28))>0){
    s.put(0x13c,5);reset(s,h);if(!call(0x472be0,0,{7}))return false;i32 selected;if(!MenuCursor{{s.data+0x28}}.move(1,selected)||!call(0x484390,0,{s.get(0x124),9}))return false;
   }}
  }
  if(sub==5||((sub==3||sub==4)&&s.get(0x13c)==5)){
   i32 duration=20;
   if(s.get(0x130)==2){if(!call(0x431f80,0x4e46f0,{}))return false;if(u32(returned)){
    if(signed_word(s.get(0x28)-5)>=4&&s.get(0x18)==1){
     if(!call(0x41af40,0,{0,0,0}))return false;const u32 handle=u32(returned);if(!h.dialog_update_write(0x4e49a0,&handle,4)||!call(0x484320,0,{handle,7})||!call(0x41ce10,0,{word(480.f),word(392.f)}))return false;
    }duration=38;
   }}
   if(signed_word(s.get(0x18))>=duration)next_page=true;
  }
  if(next_page){
   s.put(0x13c,2);reset(s,h);const u32 mode=s.get(0x130),selected=s.get(0x28);u32 start,count;
   if(!read_word(h,0x4c8020+mode*4,start)||!read_word(h,0x4c7ffc+mode*4,count))return false;
   if(signed_word(selected-start)>=signed_word(count)){s.put(0x10,2);s.put(0x13c,0);reset(s,h);}
   else if(!call(0x48aff2,0,{self+0x140,0x4c7fe8,selected})||!call(0x444ad0,0x4e47d0,{0x4683c0}))return false;
  }
 }
 return tick(s,h);
}
}
