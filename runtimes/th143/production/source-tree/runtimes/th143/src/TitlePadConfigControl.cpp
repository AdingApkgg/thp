#include "TitlePadConfigControl.hpp"
#include "MenuCursor.hpp"
#include <array>
namespace th143 {
namespace {
u32 signal_id(u32 v){const u16 s=u16(v);return s&0x8000?u32(i32(s)-65536):s;}
bool tick(AnmView t,TitleOptionControlHost& h){const u32 old=t.get(0x2b8),token=t.get(0x2c0);t.put(0x2b4,old);float rate=1;if(token&&!h.timer_rate(token,rate))return false;const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=t.floating(0x2bc)+(unit?1.f:rate);t.put(0x2b8,unit?old+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);t.put(0x2bc,word(value));return true;}
}
bool advance_title_pad_config(AnmView t,u32 self,TitleOptionControlHost& h,u32& result){
 if(!t.data||t.get(0x1c)!=4||(t.get(0xe000)&1))return false;u32 returned=0;auto call=[&](u32 e,u32 owner,std::initializer_list<u32> a){return h.title_option_call(e,owner,a,returned);};auto read=[&](u32 p,u32& v){return h.title_option_read(p,&v,4);};
 auto restore=[&](){return h.title_option_read(0x4e1c04,t.data+0x5b38,8)&&call(0x461870,self,{});};
 auto close=[&](){return call(0x472be0,0,{9})&&call(0x484320,0,{t.get(0x2d0),6})&&call(0x484320,0,{t.get(0x408),6})&&call(0x45e900,self,{4});};
 const u32 phase=t.get(0x24);MenuCursor cursor{t.sub(0x28)};
 if(phase==0){t.put(0x30,6);if(!cursor.select(0)||!call(0x45e970,self,{2})||!call(0x45e970,self,{80})||!call(0x45e900,self,{1})||!restore())return false;}
 if(phase==0||phase==1){if(signed_word(t.get(0x2b8))>6&&(!call(0x45e900,self,{2})||!call(0x484390,0,{t.get(0x2d0),3})||!call(0x484320,0,{t.get(0x2d0),signal_id(t.get(0x28)+27)})))return false;}
 else if(phase==2){
  t.put(0x2c,t.get(0x28));u32 fresh,repeated;if(!read(0x4e19dc,fresh)||!read(0x4e19d8,repeated))return false;i32 moved;if(((fresh|repeated)&0x10)&&!cursor.move(-1,moved))return false;if(((fresh|repeated)&0x20)&&!cursor.move(1,moved))return false;
  if(t.get(0x2c)!=t.get(0x28)&&(!call(0x472be0,0,{10})||!call(0x484390,0,{t.get(0x2d0),3})||!call(0x484320,0,{t.get(0x2d0),signal_id(t.get(0x28)+7)})||!call(0x484320,0,{t.get(0x408),signal_id(t.get(0x28)+7)})))return false;
  if(!call(0x401e70,0,{}))return false;const u32 buttons=returned;
  for(u32 i=0;i<31;++i){u8 value;if(!h.title_option_read(buttons+i,&value,1))return false;if(value&0x80){if(signed_word(t.get(0x28))<=3&&!assign_title_pad_button(t,self,t.get(0x28),i32(i),h))return false;break;}}
  if(!read(0x4e19dc,fresh))return false;
  if((fresh&0x102)&&t.get(0x28)==5){if(!restore()||!close())return false;}
  else if(fresh&0x80001){
   if(t.get(0x28)==4){if(!restore()||!call(0x472be0,0,{7}))return false;}
   else if(t.get(0x28)==5){std::array<u8,20> applied;if(!h.title_option_write(0x4e1c04,t.data+0x5b38,8)||!h.title_option_read(0x4e1c04,applied.data(),applied.size())||!h.title_option_write(0x4e49a8,applied.data(),applied.size())||!close())return false;}
  }
 }else if(phase==4&&signed_word(t.get(0x2b8))>=10){if(!call(0x45e880,self,{3}))return false;cursor.pop();}
 result=1;return tick(t,h);
}
}
