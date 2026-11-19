#include "TitleManualPage.hpp"
namespace th143 {
bool advance_title_manual_page(AnmView title,u32 self,TitleManualPageHost& h,u32& result){
 if(!title.data||title.get(0x1c)!=5||(title.get(0xe000)&1))return false;u32 returned=0;
 auto read=[&](u32 p,u32& value){return h.title_manual_read(p,&value,4);};auto write=[&](u32 p,u32 value){return h.title_manual_write(p,&value,4);};auto call=[&](u32 e,u32 owner,std::initializer_list<u32> args){return h.title_manual_call(e,owner,args,returned);};
 if(title.get(0x24)==0){
  if(!title.get(0x73c)){
   u32 ascii,resource,counter;if(!read(0x4e69f8,ascii)||!read(ascii+0x191e4,resource)||!read(resource+0x134,counter)||!write(resource+0x134,counter+1)||!call(0x484de0,0,{}))return false;const u32 vm=returned;
   if(!call(0x40ab20,resource,{vm,19}))return false;u32 flags;if(!read(vm+0x1c,flags)||!write(vm+0x1c,flags|0x200u)||!write(vm+0x59c,0)||!write(vm+0x5a0,0)||!write(vm+0x5a4,0)||!write(vm+0x50,0)||!call(0x474710,vm,{})||!call(0x483a70,0,{vm}))return false;title.put(0x73c,returned);
  }
  if(!call(0x45e970,self,{87})||!call(0x4347b0,0,{}))return false;title.put(0x24,1);const u32 flags=title.get(0x2c4);if(!(flags&1)){title.put(0x2c0,h.global_rate_token());title.put(0x2c4,flags|1);}title.put(0x2b8,0);title.put(0x2bc,0);title.put(0x2b4,0xffffffff);u32 manual;if(!read(0x4e6b60,manual)||!write(manual+0x12c,0x43000000))return false;
 }else if(title.get(0x24)==1){
  u32 manual,done;if(!read(0x4e6b60,manual)||!read(manual+0x128,done))return false;
  if(done){if(!call(0x484320,0,{title.get(0x73c),1}))return false;title.put(0x73c,0);if(!call(0x484320,0,{title.get(0x424),1}))return false;title.put(0x424,0);if(!call(0x45e880,self,{1})||!read(0x4e6b60,manual))return false;if(manual&&(!call(0x4346c0,manual,{})||!call(0x48a6e8,0,{manual})))return false;}
 }
 auto timer=title.sub(0x2b4);const u32 old=timer.get(4),token=timer.get(12);timer.put(0,old);float rate=1;if(token&&!h.timer_rate(token,rate))return false;const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=timer.floating(8)+(unit?1.f:rate);timer.put(4,unit?old+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);timer.put(8,word(value));result=1;return true;
}
}
