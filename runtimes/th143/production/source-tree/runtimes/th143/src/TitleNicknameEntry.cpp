#include "TitleNicknameEntry.hpp"
#include "MenuCursor.hpp"
namespace th143 {
bool advance_title_nickname_entry(TitleNicknameEntryBindings b,TitleOptionControlHost& h,u32& result){
 auto t=b.title;if(!t.data||!b.catalog.data||!b.save.data||!b.scratch.data||t.get(0x1c)!=12||(t.get(0xe000)&1)||(t.get(0x24)!=0&&t.get(0x24)!=2))return false;u32 returned=0;
 auto read=[&](u32 p,u32& v){return h.title_option_read(p,&v,4);};auto write=[&](u32 p,u32 v){return h.title_option_write(p,&v,4);};auto call=[&](u32 e,u32 owner,std::initializer_list<u32> args){return h.title_option_call(e,owner,args,returned);};
 if(t.get(0x24)==0){
  if(!t.get(0x73c)){
   u32 ascii,resource,count;if(!read(0x4e69f8,ascii)||!read(ascii+0x191e4,resource)||!read(resource+0x134,count)||!write(resource+0x134,count+1)||!call(0x484de0,0,{}))return false;const u32 vm=returned;
   if(!call(0x40ab20,resource,{vm,19}))return false;u32 flags;if(!read(vm+0x1c,flags)||!write(vm+0x1c,flags|0x200u)||!write(vm+0x59c,0)||!write(vm+0x5a0,0)||!write(vm+0x5a4,0)||!write(vm+0x50,0)||!call(0x474710,vm,{})||!call(0x483a70,0,{vm}))return false;t.put(0x73c,returned);
  }
  if(!call(0x45e900,b.self,{1}))return false;t.put(0x30,70);t.put(0xf8,1);if(!MenuCursor{t.sub(0x28)}.select(0))return false;
  for(u32 script:{85,213,214,215,216})if(!call(0x45e970,b.self,{script}))return false;
  u32 name;if(!lookup_trophy_name(b.catalog,t.get(0x28),b.scratch,name))return false;
  if(name){
   const u32 unlocked=b.save.data[0xeff9+t.get(0x28)]!=0;if(unlocked&&!lookup_trophy_name(b.catalog,t.get(0x28),b.scratch,name))return false;if(!unlocked)name=0x4c7d08;
   u32 pool;if(!read(0x538de8,pool)||!call(0x484280,pool,{t.get(0x61c)}))return false;u32 vm=returned;if(!vm)t.put(0x61c,0);if(!read(0x538de8,pool)||!call(0x482e40,0,{pool,vm,0xffffff,0,4,0,name}))return false;
   for(u32 line=0;line<3;++line){const u32 index=t.get(0x28),at=0x620+line*4;if(!read(0x538de8,pool)||!call(0x484280,pool,{t.get(at)}))return false;vm=returned;if(!vm)t.put(at,0);u32 text;if(!lookup_trophy_description(b.catalog,index,unlocked,line,b.scratch,text)||!read(0x538de8,pool)||!call(0x482e40,0,{pool,vm,0xffffff,0,4,0,text}))return false;}
  }
 }else if(signed_word(t.get(0x2b8))>=20){if(!call(0x484320,0,{t.get(0x73c),1}))return false;t.put(0x73c,0);if(!call(0x45e880,b.self,{1}))return false;MenuCursor{t.sub(0x28)}.pop();}
 const u32 previous=t.get(0x2b8),token=t.get(0x2c0);t.put(0x2b4,previous);float rate=1;if(token&&!h.timer_rate(token,rate))return false;const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float next=t.floating(0x2bc)+(unit?1.f:rate);t.put(0x2b8,unit?previous+1:next>=-2147483648.f&&next<2147483648.f?u32(i32(next)):0x80000000);t.put(0x2bc,word(next));result=1;return true;
}
}
