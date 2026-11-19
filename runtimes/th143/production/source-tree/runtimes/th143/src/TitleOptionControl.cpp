#include "TitleOptionControl.hpp"
#include "MenuCursor.hpp"
namespace th143 {
namespace {
i32 short_signal(u32 v){const u16 s=u16(v);return s&0x8000?i32(s)-65536:i32(s);}
i32 signed_byte(u8 v){return v&0x80?i32(v)-256:i32(v);}
bool tick(AnmView t,TitleOptionControlHost& h){const u32 old=t.get(0x2b8),token=t.get(0x2c0);t.put(0x2b4,old);float rate=1;if(token&&!h.timer_rate(token,rate))return false;const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=t.floating(0x2bc)+(unit?1.f:rate);t.put(0x2b8,unit?old+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);t.put(0x2bc,word(value));return true;}
}
bool advance_title_option_control(AnmView t,u32 self,TitleOptionControlHost& h,u32& result){
 if(!t.data||t.get(0x1c)!=3||(t.get(0xe000)&1))return false;u32 returned=0;auto call=[&](u32 e,u32 owner,std::initializer_list<u32> a){return h.title_option_call(e,owner,a,returned);};auto read=[&](u32 p,u32& v){return h.title_option_read(p,&v,4);};
 auto selection=[&](){return call(0x484390,0,{t.get(0x2cc),3})&&call(0x484320,0,{t.get(0x2cc),u32(short_signal(t.get(0x28)+7))})&&call(0x484320,0,{t.get(0x404),u32(short_signal(t.get(0x28)+7))});};
 auto leave=[&](u32 sound){return call(0x484320,0,{t.get(0x2cc),6})&&call(0x484320,0,{t.get(0x404),6})&&call(0x472be0,0,{sound})&&call(0x45e900,self,{4});};
 const u32 phase=t.get(0x24);MenuCursor cursor{t.sub(0x28)};
 if(phase==0){t.put(0x30,5);if(!cursor.select(0)||!call(0x45e970,self,{1})||!call(0x45e970,self,{79})||!call(0x460540,self,{})||!call(0x45e900,self,{1}))return false;}
 if(phase==0||phase==1){if(signed_word(t.get(0x2b8))>6){if(!call(0x45e900,self,{2})||!call(0x484390,0,{t.get(0x2cc),3})||!call(0x484320,0,{t.get(0x2cc),u32(short_signal(t.get(0x28)+27))}))return false;}}
 else if(phase==2){
  t.put(0x2c,t.get(0x28));u32 fresh,repeated;if(!read(0x4e19dc,fresh)||!read(0x4e19d8,repeated))return false;i32 moved;if(((fresh|repeated)&0x10)&&!cursor.move(-1,moved))return false;if(((fresh|repeated)&0x20)&&!cursor.move(1,moved))return false;
  if(t.get(0x2c)!=t.get(0x28)&&(!call(0x472be0,0,{10})||!selection()))return false;if(!read(0x4e19dc,fresh))return false;
  if(fresh&0x102){if(t.get(0x28)==4){if(!leave(9))return false;}else{if(!call(0x472be0,0,{9})||!cursor.select(4)||!selection())return false;}result=1;return tick(t,h);}
  if(t.get(0x28)==1&&t.get(0x2b8)!=t.get(0x2b4)&&signed_word(t.get(0x2b8))%60==0&&!call(0x472be0,0,{2}))return false;
  if(!read(0x4e19dc,fresh)||!read(0x4e19d8,repeated))return false;
  auto volume=[&](bool right){const u32 row=t.get(0x28);if(row>1)return true;const u32 p=0x4e49c6+row;u8 v;if(!h.title_option_read(p,&v,1))return false;if(right){v=u8(v+5);if(signed_byte(v)>100)v=100;}else v=signed_byte(v)>=5?u8(v-5):0;return h.title_option_write(p,&v,1)&&call(0x460540,self,{});};
  if(((fresh|repeated)&0x40)&&!volume(false))return false;if(!read(0x4e19dc,fresh)||!read(0x4e19d8,repeated))return false;if(((fresh|repeated)&0x80)&&!volume(true))return false;if(!read(0x4e19dc,fresh))return false;
  if(fresh&0x80001){const u32 row=t.get(0x28);if(row==2){if(!leave(7))return false;}else if(row==3){const u8 defaults[]={100,80,0};if(!h.title_option_write(0x4e49c6,defaults,3)||!call(0x460540,self,{})||!call(0x472be0,0,{7}))return false;}else if(row==4&&!leave(9))return false;}
 }else if(phase==4&&signed_word(t.get(0x2b8))>=10){const u32 row=t.get(0x28);if(row==4){if(!call(0x45e880,self,{1}))return false;cursor.pop();}else if(row==2){if(!call(0x45e880,self,{4})||!cursor.push())return false;}}
 result=1;return tick(t,h);
}
}
