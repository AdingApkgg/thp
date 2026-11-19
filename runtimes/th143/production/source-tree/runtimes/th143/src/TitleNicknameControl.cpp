#include "TitleNicknameControl.hpp"
namespace th143 {
namespace {
struct NicknameControl {
 TitleNicknameEntryBindings b;TitleOptionControlHost& h;u32 returned=0;
 AnmView title(){return b.title;}
 bool read(u32 p,u32& v){return h.title_option_read(p,&v,4);}bool write(u32 p,u32 v){return h.title_option_write(p,&v,4);}
 bool call(u32 e,u32 owner,std::initializer_list<u32> args){return h.title_option_call(e,owner,args,returned);}
 bool backdrop(){auto t=title();if(t.get(0x73c))return true;u32 ascii,resource,count;if(!read(0x4e69f8,ascii)||!read(ascii+0x191e4,resource)||!read(resource+0x134,count)||!write(resource+0x134,count+1)||!call(0x484de0,0,{}))return false;const u32 vm=returned;
  if(!call(0x40ab20,resource,{vm,19}))return false;u32 flags;if(!read(vm+0x1c,flags)||!write(vm+0x1c,flags|0x200u)||!write(vm+0x59c,0)||!write(vm+0x5a0,0)||!write(vm+0x5a4,0)||!write(vm+0x50,0)||!call(0x474710,vm,{})||!call(0x483a70,0,{vm}))return false;t.put(0x73c,returned);return true;
 }
 bool text(){auto t=title();u32 name;if(!lookup_trophy_name(b.catalog,t.get(0x28),b.scratch,name))return false;if(!name)return true;const u32 unlocked=b.save.data[0xeff9+t.get(0x28)]!=0;if(unlocked&&!lookup_trophy_name(b.catalog,t.get(0x28),b.scratch,name))return false;if(!unlocked)name=0x4c7d08;
  if(!call(0x4845f0,b.self+0x61c,{}))return false;u32 vm=returned,pool;if(!read(0x538de8,pool)||!call(0x482e40,0,{pool,vm,0xffffff,0,4,0,name}))return false;
  for(u32 line=0;line<3;++line){const u32 index=t.get(0x28);u32 text;if(!lookup_trophy_description(b.catalog,index,unlocked,line,b.scratch,text)||!call(0x4845f0,b.self+0x620+line*4,{}))return false;vm=returned;if(!read(0x538de8,pool)||!call(0x482e40,0,{pool,vm,0xffffff,0,4,0,text}))return false;}return true;
 }
 bool raw_sequence(){auto t=title();if(t.get(0x28)!=17)return true;u32 fresh;if(!read(0x4e19dc,fresh))return false;if(fresh&0x80103)if(!write(0x540f24,0)||!write(0x540f20,0))return false;
  std::array<u8,256> current,previous,pressed;if(!h.title_option_read(0x541160,current.data(),256)||!h.title_option_write(0x541260,current.data(),256)||!call(0x402af0,0,{}))return false;const u32 mode=returned;
  if(mode==2){if(!h.title_option_read(0x541160,current.data(),256))return false;std::array<u8,256> converted{};constexpr u8 scan[]={0x1e,0x30,0x2e,0x20,0x12,0x21,0x22,0x23,0x17,0x24,0x25,0x26,0x32,0x31,0x18,0x19,0x10,0x13,0x1f,0x14,0x16,0x2f,0x11,0x2d,0x15,0x2c};for(u32 i=0;i<26;++i)converted[scan[i]]=current[0x41+i];if(!h.title_option_write(0x541160,converted.data(),256))return false;}
  u32 clock=0;bool reset_clock=false;
  if(mode==1||mode==2){if(!h.title_option_read(0x541160,current.data(),256)||!h.title_option_read(0x541260,previous.data(),256))return false;for(u32 i=0;i<256;++i)pressed[i]=(current[i]^previous[i])&current[i];if(!h.title_option_write(0x540e20,pressed.data(),256))return false;
   u32 index;if(!read(0x540f24,index))return false;if(index>=9){const u16 flags=0x102;std::memcpy(b.save.data+0xefac,&flags,2);b.save.put(0xf084,9);if(!call(0x472be0,0,{17})||!write(0x540f24,0))return false;}
   else{u32 scan;if(!read(0x4c7e94+index*4,scan)||scan>=256)return false;if(pressed[scan]&0x80){if(!write(0x540f24,index+1))return false;reset_clock=true;}else{u8 any=0;for(u32 i=0;i<0x39;++i)any|=pressed[i];if(!write(0x540f24,any&0x80?0:index))return false;}}
  }
  if(!reset_clock&&!read(0x540f20,clock))return false;++clock;if(!write(0x540f20,clock))return false;if(signed_word(clock)>300)return write(0x540f24,0)&&write(0x540f20,0);return true;
 }
 bool body(){auto t=title();u32 notice;if(!read(0x4e6b80,notice))return false;
  if(notice){u32 done;if(!read(notice+0x118,done))return false;if(!done)return true;if(!call(0x446d00,notice,{})||!call(0x48a6e8,0,{notice})||!backdrop()||!call(0x45e970,b.self,{85}))return false;for(u32 at:{0x61c,0x620,0x624,0x628})if(!call(0x484320,0,{t.get(at),4}))return false;return call(0x444660,0,{0x4c7b2c})&&call(0x4446e0,0,{0,0});}
  const u32 count=b.save.get(0xf16c);if(signed_word(count)>0){if(count>16)return false;if(b.save.get(0xf16c+count*4)==39){b.save.put(0xf16c,count-1);const u32 id=b.save.get(0xf170+(count-1)*4);if(!call(0x446e20,id,{}))return false;u32 flags;if(!read(0x4e49dc,flags)||!call(0x4737b0,0x53b1e0,{flags&0x10?4u:3u,0,0x4c61a4})||!call(0x484320,0,{t.get(0x73c),1}))return false;t.put(0x73c,0);if(!call(0x45ea30,b.self,{85}))return false;for(u32 at:{0x61c,0x620,0x624,0x628})if(!call(0x484320,0,{t.get(at),5}))return false;return true;}}
  u32 fresh,repeated;if(!read(0x4e19dc,fresh)||!read(0x4e19d8,repeated)||!navigate_trophy_grid(t,b.save,fresh,repeated))return false;if(t.get(0x2c)!=t.get(0x28)&&(!call(0x472be0,0,{10})||!text()))return false;
  if(signed_word(b.save.get(0xef2c))>=75&&t.get(0x28)==0){if(!read(0x4e19dc,fresh))return false;if(fresh&0x80001){const u32 pending=b.save.get(0xf16c);if(pending>=16)return false;b.save.put(0xf170+pending*4,39);b.save.put(0xf16c,pending+1);}}
  if(!read(0x4e19dc,fresh))return false;if(fresh&0x102){if(!call(0x45e900,b.self,{2})||!call(0x472be0,0,{9}))return false;for(u32 at:{0x61c,0x620,0x624,0x628,0x41c}){if(!call(0x484320,0,{t.get(at),1}))return false;t.put(at,0);}}
  return raw_sequence();
 }
};
}
bool advance_title_nickname_control(TitleNicknameEntryBindings b,TitleOptionControlHost& h,u32& result){auto t=b.title;if(!t.data||!b.catalog.data||!b.save.data||!b.scratch.data||t.get(0x1c)!=12||t.get(0x24)!=1||(t.get(0xe000)&1))return false;NicknameControl c{b,h};if(!c.body())return false;
 const u32 previous=t.get(0x2b8),token=t.get(0x2c0);t.put(0x2b4,previous);float rate=1;if(token&&!h.timer_rate(token,rate))return false;const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float next=t.floating(0x2bc)+(unit?1.f:rate);t.put(0x2b8,unit?previous+1:next>=-2147483648.f&&next<2147483648.f?u32(i32(next)):0x80000000);t.put(0x2bc,word(next));result=1;return true;}
}
