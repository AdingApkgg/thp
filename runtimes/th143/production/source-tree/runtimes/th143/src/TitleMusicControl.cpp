#include "TitleMusicControl.hpp"
#include "MenuCursor.hpp"
#include <cmath>
namespace th143 {
namespace {
void reset(AnmView t,TitleMusicControlHost& h){const u32 flags=t.get(0x2c4);if(!(flags&1)){t.put(0x2c0,h.global_rate_token());t.put(0x2c4,flags|1);}t.put(0x2b4,0xffffffff);t.put(0x2b8,0);t.put(0x2bc,0);}
bool tick(AnmView t,TitleMusicControlHost& h){const u32 old=t.get(0x2b8),token=t.get(0x2c0);t.put(0x2b4,old);float rate=1;if(token&&!h.timer_rate(token,rate))return false;const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=t.floating(0x2bc)+(unit?1.f:rate);t.put(0x2b8,unit?old+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);t.put(0x2bc,word(value));return true;}
}
bool advance_title_music_control(AnmView t,u32 self,TitleMusicControlHost& h,u32& result){
 if(!t.data||t.get(0x1c)!=6||(t.get(0xe000)&1)||t.get(0x24)<1||t.get(0x24)>3)return false;u32 returned=0;
 auto read=[&](u32 p,u32& v){return h.title_music_read(p,&v,4);};auto write=[&](u32 p,u32 v){return h.title_music_write(p,&v,4);};auto call=[&](u32 e,u32 owner,std::initializer_list<u32> a){return h.title_music_call(e,owner,a,returned);};
 auto heard=[&](u32 index,bool& yes){u32 save;u8 value;if(!read(0x4e6b9c,save)||!h.title_music_read(save+0xef74+index,&value,1))return false;yes=value!=0;return true;};
 auto display_comment=[&](){
  if((t.get(0x2b8)&1)||signed_word(t.get(0x7f8))>=8)return true;
  if(!call(0x4845f0,self+0x7d0+t.get(0x7f8)*4,{}))return false;const u32 vm=returned;bool unlocked;if(!heard(t.get(0x7fc),unlocked))return false;u32 text,color;
  if(!unlocked&&t.get(0x800)){if(!read(0x4c7e74+t.get(0x7f8)*4,text))return false;color=0x8080ff;}
  else{text=self+0x1844+(t.get(0x7f8)+t.get(0x7fc)*8)*0x42;color=0xffffff;}
  u32 pool;if(!read(0x538de8,pool)||!call(0x482c20,0,{pool,vm,color,0,0,0,0,text})||!call(0x410ea0,vm,{2}))return false;t.put(0x7f8,t.get(0x7f8)+1);return true;
 };
 const u32 phase=t.get(0x24);
 if(phase==1){if(!display_comment())return false;if(signed_word(t.get(0x2b8))>4&&!call(0x45e900,self,{2}))return false;}
 else if(phase==2){
  if(!display_comment())return false;t.put(0x2c,t.get(0x28));u32 fresh,repeated;if(!read(0x4e19dc,fresh)||!read(0x4e19d8,repeated))return false;MenuCursor cursor{t.sub(0x28)};i32 moved;
  if(((fresh|repeated)&0x10)&&!cursor.move(-1,moved))return false;if(((fresh|repeated)&0x20)&&!cursor.move(1,moved))return false;
  if(t.get(0x2c)!=t.get(0x28)){
   if(!call(0x472be0,0,{10}))return false;const i32 selected=signed_word(t.get(0x28)),scroll=signed_word(t.get(0x5a44));if(selected<scroll)t.put(0x5a44,u32(selected));else if(selected>=scroll+10)t.put(0x5a44,u32(selected-9));
   u32 a,b,c,d,e;double indent;if(!read(0x4c9ee0,a)||!read(0x4c9ef0,b)||!read(0x4c9e94,c)||!read(0x4c9e08,d)||!read(0x4c9edc,e)||!h.title_music_read(0x4c9e30,&indent,8))return false;
   float x=real(b),product=float(signed_word(t.get(0x5a44)))*real(c),y=(real(a)-product)*real(d);u32 step;if(!read(0x4c9eb8,step))return false;
   for(u32 i=0;signed_word(i)<signed_word(t.get(0x7f4));++i){
    u32 pool;if(!read(0x538de8,pool)||!call(0x484280,pool,{t.get(0x780+i*4)}))return false;const u32 vm=returned;if(!vm){t.put(0x780+i*4,0);return false;}
    u32 flags;if(!read(vm+0x18,flags))return false;const i32 first=signed_word(t.get(0x5a44));const bool visible=signed_word(i)>=first&&signed_word(i)<first+10;if(!write(vm+0x18,visible?flags|2:flags&~2u))return false;
    if(i==t.get(0x28))x=float(double(x)-indent);u32 oldY;if(!read(vm+0x40,oldY))return false;const float delta=real(oldY)-y;
    if(real(e)>std::fabs(delta)){if(!call(0x418300,vm,{4,0,vm+0x3c,word(x),word(y),0}))return false;}
    else if(!write(vm+0x3c,word(x))||!write(vm+0x40,word(y))||!write(vm+0x44,0))return false;
    if(i==t.get(0x28))x=float(double(x)+indent);const u32 signal=i==t.get(0x28)?2u:3u;y+=real(step);u32 callback;if(!read(vm+0x5c4,callback))return false;if(callback&&!call(callback,vm,{signal}))return false;if(!write(vm+0x4a0,signal))return false;
   }
   if(signed_word(t.get(0x7f8))>=8)t.put(0x800,0);
  }
  if(!read(0x4e19dc,fresh))return false;
  if(fresh&0x80001){
   for(u32 i=0;i<8;++i)if(!call(0x484320,0,{t.get(0x7d0+i*4),3}))return false;t.put(0x7fc,t.get(0x28));t.put(0x7f8,0);reset(t,h);bool unlocked;if(!heard(t.get(0x7fc),unlocked))return false;
   u32 config;if(!unlocked&&!t.get(0x800)){
    if(!read(0x4e49dc,config)||!call(0x4737b0,0x53b1e0,{config&0x10?4u:3u,0,0x4c61a4}))return false;t.put(0x800,1);
   }else{
    if(!call(0x444660,0,{self+0x804+(t.get(0x28)<<6)})||!read(0x4e49dc,config))return false;
    if((config&0x10)&&!call(0x4737b0,0x53b1e0,{4,0,0x4c61a4}))return false;if(!call(0x4737b0,0x53b1e0,{2,0,0x4c61a4}))return false;
    u32 save;if(!read(0x4e6b9c,save))return false;const u8 one=1;if(!h.title_music_write(save+0xef74,&one,1))return false;t.put(0x800,0);
   }
  }else if(fresh&0x102){
   if(t.get(0x5ce4)){if(!call(0x48a7bc,0,{t.get(0x5ce4)}))return false;t.put(0x5ce4,0);}t.put(0x5ce4,0);
   for(u32 i=0;signed_word(i)<signed_word(t.get(0x7f4));++i)if(!call(0x484320,0,{t.get(0x780+i*4),1}))return false;
   for(u32 i=0;i<8;++i)if(!call(0x484320,0,{t.get(0x7d0+i*4),1}))return false;if(!call(0x472be0,0,{9}))return false;t.put(0x24,3);reset(t,h);
  }
 }else if(signed_word(t.get(0x2b8))>=10){
  if(!call(0x484320,0,{t.get(0x420),1}))return false;t.put(0x420,0);if(!call(0x484320,0,{t.get(0x73c),1}))return false;t.put(0x73c,0);
  if(!call(0x45e880,self,{1})||!call(0x444660,0,{0x4c7b2c})||!call(0x4446e0,0,{0,0}))return false;MenuCursor{t.sub(0x28)}.pop();
 }
 result=1;return tick(t,h);
}
}
