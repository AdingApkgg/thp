#include "NoticeUpdate.hpp"
namespace th143 {
namespace {
void reset(AnmView t){u32 flags=t.get(16);if(!(flags&1)){t.put(12,0x4e40b0);t.put(16,flags|1);}t.put(0,0xffffffff);t.put(4,0);t.put(8,0);}
bool tick(AnmView t,NoticeUpdateHost& h){const u32 old=t.get(4),token=t.get(12);float rate=1;if(token&&!h.timer_rate(token,rate))return false;t.put(0,old);const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));float value=t.floating(8)+(unit?1.f:rate);t.put(8,word(value));t.put(4,unit?old+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);return true;}
}
bool update_notice(AnmView s,u32 fresh,NoticeUpdateHost& h){
 const u32 main=s.get(0x10);auto timer=s.sub(0x14);auto cursor=MenuCursor{s.sub(0x28)};
 if(main==0)s.put(0x10,1);
 else if(main==1){
  const u32 sub=s.get(0x130);
  if(sub==0){
   s.put(0x30,99);if(!cursor.select(signed_word(s.get(0x120))))return false;s.put(0xf8,1);
   u32 table;if(!h.notice_read_word(s.get(0x124)+0x124,table)||!h.notice_texture_reset(table+0x18))return false;
   s.put(0x130,1);if(!h.notice_sound(s.get(0x120)==39?87:78))return false;
   reset(timer);s.put(0x130,2);
   if(s.get(0x120)==39){if(!h.notice_worker(0x446bb0))return false;}
   else if(!h.notice_format(reinterpret_cast<char*>(s.data+0x134),128,signed_word(s.get(0x28)))||!h.notice_worker(0x446b60))return false;
  }else if(sub==3){
   u32 table,texture;if(!h.notice_read_word(s.get(0x124)+0x124,table)||!h.notice_texture_upload(table+0x18,s.get(0x12c),s.get(0x1b4),1))return false;
   if(s.get(0x12c)){if(!h.notice_free_file(s.get(0x12c)))return false;s.put(0x12c,0);}s.put(0x12c,0);
   if(!h.notice_read_word(s.get(0x124)+0x124,table)||!h.notice_read_word(table+0x18,texture)||!h.notice_texture_release(texture))return false;
   for(i32 script=0;script<=4;script+=4){u32 handle;if(!h.notice_animation(s.get(0x124),script,handle))return false;s.put(0x100+u32(script)*4,handle);}
   s.put(0x130,4);reset(timer);
  }else if(sub==4){
   if(signed_word(s.get(0x18))>=20&&(fresh&0x80001)&&signed_word(s.get(0x28))>0){
    s.put(0x10,2);s.put(0x130,0);reset(timer);if(!h.notice_sound(7))return false;i32 ignored;if(!cursor.move(1,ignored)||!h.notice_signal(s.get(0x110),1)||!h.notice_signal(s.get(0x100),1))return false;
   }
  }else if(sub==5){
   if(signed_word(s.get(0x18))>=20){s.put(0x130,2);reset(timer);if(s.get(0x120)==39){if(!h.notice_worker(0x446bb0))return false;}else if(!h.notice_format(reinterpret_cast<char*>(s.data+0x134),128,signed_word(s.get(0x28)))||!h.notice_worker(0x446b60))return false;}
  }else if(sub==6){
   const u32 resource=s.get(0x128);u32 token,handle;AnmView vm;
   if(!h.notice_resource_increment(resource)||!h.notice_allocate_vm(token,vm)||!vm.data||!h.notice_initialize_vm(resource,token,0))return false;
   vm.put(0x1c,vm.get(0x1c)|0x200);vm.put(0x59c,0);vm.put(0x5a0,0);vm.put(0x5a4,0);vm.put(0x50,0);
   if(!h.notice_update_vm(token)||!h.notice_register_vm(token,handle))return false;
   s.put(0x114,handle);s.put(0x130,7);reset(timer);
  }else if(sub==7){
   if(signed_word(s.get(0x18))>=240&&(fresh&0x80001)&&signed_word(s.get(0x28))>0){
    s.put(0x10,3);s.put(0x130,0);reset(timer);if(!h.notice_sound(7))return false;i32 ignored;if(!cursor.move(1,ignored)||!h.notice_signal(s.get(0x114),1))return false;
   }
  }
 }else if((main==2&&signed_word(s.get(0x18))>=30)||(main==3&&signed_word(s.get(0x18))>=240))s.put(0x118,1);
 return tick(timer,h);
}
}
