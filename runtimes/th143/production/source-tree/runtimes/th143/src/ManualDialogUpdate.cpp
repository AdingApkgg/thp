#include "ManualDialogUpdate.hpp"
#include "MenuCursor.hpp"
namespace th143 {
namespace {
bool read_word(ManualDialogUpdateHost& h,u32 p,u32& v){return h.manual_update_read(p,&v,4);}
void reset(AnmView s,ManualDialogUpdateHost& h){const u32 flags=s.get(0x24);if(!(flags&1)){s.put(0x20,h.global_rate_token());s.put(0x24,flags|1);}s.put(0x14,0xffffffff);s.put(0x18,0);s.put(0x1c,0);}
bool tick(AnmView s,ManualDialogUpdateHost& h){const u32 token=s.get(0x20),old=s.get(0x18);s.put(0x14,old);float rate=1;if(token&&!h.timer_rate(token,rate))return false;const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=s.floating(0x1c)+(unit?1.f:rate);s.put(0x18,unit?old+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);s.put(0x1c,word(value));return true;}
}
bool update_manual_dialog(AnmView s,u32 self,ManualDialogUpdateHost& h,i32& result){
 result=1;u32 returned=0;const u32 x=s.get(0x12c);auto call=[&](u32 e,u32 owner,std::initializer_list<u32> args){return h.manual_update_call(e,owner,args,returned);};
 auto resource_texture=[&](u32& descriptor){return read_word(h,s.get(0x130)+0x124,descriptor);};
 auto make_menu=[&](){for(u32 i=0;i<5;++i){if(!call(0x432000,s.get(0x130),{i,x,0,0}))return false;const u32 handle=returned;s.put(0x100+i*4,handle);if(!call(0x484390,0,{handle,s.get(0x28)==i?2u:3u}))return false;}return true;};
 auto remove_menu=[&](){for(u32 i=0;i<5;++i)if(!call(0x484320,0,{s.get(0x100+i*4),1}))return false;return true;};
 auto next_page=[&](){s.put(0x138,2);reset(s,h);return call(0x48aff2,0,{self+0x13c,0x4c58c4,s.get(0x28)+1})&&call(0x444ad0,0x4e47d0,{0x434570})&&remove_menu();};
 const u32 main=s.get(0x10);
 if(main==0)s.put(0x10,1);
 else if(main==2){if(signed_word(s.get(0x18))>=30)s.put(0x128,1);}
 else if(main==1){
  u32 sub=s.get(0x138);
  if(sub==0){s.put(0x30,5);if(!MenuCursor{{s.data+0x28}}.select(0))return false;s.put(0xf8,1);if(!make_menu())return false;u32 descriptor;if(!resource_texture(descriptor)||!call(0x484a40,descriptor+0x18,{}))return false;s.put(0x138,1);sub=1;}
  if(sub==1&&signed_word(s.get(0x18))>=20){
   s.put(0x2c,s.get(0x28));u32 fresh,repeated;if(!read_word(h,0x4e19dc,fresh)||!read_word(h,0x4e19d8,repeated))return false;MenuCursor cursor{{s.data+0x28}};i32 selected;
   if(((fresh|repeated)&0x10)&&!cursor.move(-1,selected))return false;if(((fresh|repeated)&0x20)&&!cursor.move(1,selected))return false;
   if(s.get(0x2c)!=s.get(0x28)){if(!call(0x472be0,0,{10}))return false;for(u32 i=0;i<5;++i)if(!call(0x484390,0,{s.get(0x100+i*4),s.get(0x28)==i?2u:3u}))return false;}
   if(!read_word(h,0x4e19dc,fresh))return false;
   if(fresh&0x80001){if(!call(0x472be0,0,{7})||!next_page())return false;}
   else if(fresh&0x102){if(!call(0x472be0,0,{9})||!remove_menu())return false;s.put(0x10,2);s.put(0x138,0);reset(s,h);}
  }else if(sub==3){
   u32 descriptor;if(!resource_texture(descriptor)||!call(0x481990,0,{descriptor+0x18,s.get(0x134),s.get(0x1bc),1}))return false;
   if(s.get(0x134)){if(!call(0x48a7bc,0,{s.get(0x134)}))return false;s.put(0x134,0);}s.put(0x134,0);u32 texture;if(!resource_texture(descriptor)||!read_word(h,descriptor+0x18,texture)||!call(0x24,texture,{}))return false;
   if(!call(0x432000,s.get(0x130),{9,x,0,0}))return false;s.put(0x124,returned);s.put(0x138,4);reset(s,h);sub=4;
  }
  if(sub==4&&signed_word(s.get(0x18))>=20){
   u32 fresh;if(!read_word(h,0x4e19dc,fresh))return false;const bool down=(fresh&0x20)&&signed_word(s.get(0x28))<4,up=!down&&(fresh&0x10)&&signed_word(s.get(0x28))>0;
   if(down||up){s.put(0x138,5);reset(s,h);if(!call(0x472be0,0,{7}))return false;i32 selected;if(!MenuCursor{{s.data+0x28}}.move(down?1:-1,selected)||!call(0x484390,0,{s.get(0x124),down?7u:8u}))return false;sub=5;}
   else if(fresh&0x80103){if(!call(0x472be0,0,{9}))return false;s.put(0x138,1);reset(s,h);if(!call(0x484320,0,{s.get(0x124),1})||!make_menu())return false;}
  }
  if(sub==5&&signed_word(s.get(0x18))>=20&&!next_page())return false;
 }
 return tick(s,h);
}
}
