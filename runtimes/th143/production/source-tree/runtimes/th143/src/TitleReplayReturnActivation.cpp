#include "TitleReplayReturnActivation.hpp"
#include "MenuCursor.hpp"
namespace th143 {
bool activate_returned_title_replay(AnmView t,u32 self,TitleOptionControlHost& h,u32& result){
 if(!t.data||t.get(0x1c)||(t.get(0xe000)&1))return false;u32 returned=0;
 auto read=[&](u32 p,u32& v){return h.title_option_read(p,&v,4);};auto write=[&](u32 p,u32 v){return h.title_option_write(p,&v,4);};auto call=[&](u32 e,u32 o,std::initializer_list<u32> a){return h.title_option_call(e,o,a,returned);};u32 mode;if(!read(0x4e6bb0,mode)||mode!=2||!call(0x467520,0x4e49a0,{}))return false;
 if(returned){u32 ascii,handle;if(!read(0x4e69f8,ascii)||!read(ascii+0x191e8,handle)||!call(0x484320,0,{handle,1})||!call(0x41cd10,0,{})||!read(0x4e49a0,handle)||!call(0x484320,0,{handle,1})||!write(0x4e49a0,0))return false;t.put(0xe000,t.get(0xe000)|0x40);}
 u32 trophy,save,pending;if(!call(0x41cd10,0,{})||!read(0x4e6b80,trophy)||trophy||!read(0x4e6b9c,save)||!save||!read(save+0xf16c,pending))return false;
 if(signed_word(pending)>0){u32 last;if(pending>16||!read(save+0xf16c+pending*4,last)||last==39)return false;}
 u32 pool;if(!read(0x538de8,pool))return false;for(u32 offset:{0xbc7b20,0xbc7b28,0xbc7b14,0xbc7b0c}){u32 resource;if(!read(pool+offset,resource)||!call(0x484590,pool,{resource}))return false;}
 u32 cheat,callback,flags;if(!read(0x4e6b68,cheat)||!read(cheat+8,callback)||!read(callback+4,flags)||!write(callback+4,flags|2)||!read(cheat+12,callback)||!read(callback+4,flags)||!write(callback+4,flags|2)||!read(0x4e47b0,flags))return false;
 if(flags&0x80){u32 cached;t.put(0xe000,t.get(0xe000)&~1u);if(!read(0x4e4798,cached)||!write(0x4e46fc,cached))return false;}else{t.put(0xe000,t.get(0xe000)|1);t.put(0xdffc,0);}
 if(!read(0x4e47b0,flags)||!write(0x4e47b0,flags&~0x80u)||!read(0x4e6bb0,mode)||mode!=2)return false;t.put(0xe000,t.get(0xe000)&~2u);
 if(!call(0x444660,0,{0,0x4c7b2c})||!call(0x4446e0,0,{0,0})||!call(0x44b7b0,0x4e46f0,{0}))return false;t.put(0x30,10);MenuCursor cursor{t.sub(0x28)};if(!cursor.select(1)||!cursor.push()||!call(0x45e880,self,{7})||!write(0x4e6bb0,1)||!read(self+0x10,callback)||!read(callback+4,flags)||!write(callback+4,flags|2)||!call(0x4650c0,self,{}))return false;
 const u32 old=t.get(0x2b8),token=t.get(0x2c0);t.put(0x2b4,old);float rate=1;if(token&&!h.timer_rate(token,rate))return false;const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=t.floating(0x2bc)+(unit?1.f:rate);t.put(0x2b8,unit?old+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);t.put(0x2bc,word(value));result=1;return true;
}
}
