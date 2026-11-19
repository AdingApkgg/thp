#include "TitleReplayControlV2.hpp"
#include "MenuCursor.hpp"
namespace th143 {
namespace {
struct ReplayControl {
 AnmView t;u32 self;TitleOptionControlHost& h;u32 returned=0;
 bool read(u32 p,u32& v){return h.title_option_read(p,&v,4);}bool write(u32 p,u32 v){return h.title_option_write(p,&v,4);}
 bool call(u32 e,u32 owner,std::initializer_list<u32> a){return h.title_option_call(e,owner,a,returned);}
 bool backdrop(){if(t.get(0x73c))return true;u32 ascii,resource,count;if(!read(0x4e69f8,ascii)||!read(ascii+0x191e4,resource)||!read(resource+0x134,count)||!write(resource+0x134,count+1)||!call(0x484de0,0,{}))return false;const u32 vm=returned;
  if(!call(0x40ab20,resource,{vm,19}))return false;u32 flags;if(!read(vm+0x1c,flags)||!write(vm+0x1c,flags|0x200)||!write(vm+0x59c,0)||!write(vm+0x5a0,0)||!write(vm+0x5a4,0)||!write(vm+0x50,0)||!call(0x474710,vm,{})||!call(0x483a70,0,{vm}))return false;t.put(0x73c,returned);return true;
 }
 bool confirm(MenuCursor& cursor){t.put(0x5b50,t.get(0x28));u32 fade;if(!call(0x45e900,self,{3}))return false;t.put(0xe000,t.get(0xe000)|4);return call(0x472be0,0,{50})&&read(0x4c9cd0,fade)&&call(0x444810,0,{fade});}
 bool body(){const u32 phase=t.get(0x24);MenuCursor row{t.sub(0x28)},page{t.sub(0x1d8)};i32 moved;
  if(phase==0){u32 remembered;if(!read(0x4e6bc0,remembered))return false;const i32 selected=signed_word(remembered),p=selected/25;t.put(0x30,25);if(!row.select(selected-p*25))return false;t.put(0x1e0,3);if(!page.select(p))return false;t.put(0x2a8,1);if(!write(0x4e6bc0,0)||!backdrop()||!call(0x45e970,self,{84})||!call(0x45e900,self,{1}))return false;std::memset(t.data+0x5b54,0,0x190);t.put(0xe000,t.get(0xe000)&~12u);t.put(0x5b48,0);if(!call(0x403f10,self+0xe0f8,{0x4650b0,self}))return false;u32 pool;if(!read(0x538de8,pool)||!call(0x484280,pool,{t.get(0x454)}))return false;if(!returned&&(!call(0x45e970,self,{99})||!call(0x484390,0,{t.get(0x454),3})))return false;}
  if(phase==0||phase==1){if(signed_word(t.get(0x2b8))>6&&!call(0x45e900,self,{2}))return false;return true;}
  if(phase==2){t.put(0x2c,t.get(0x28));t.put(0x1dc,t.get(0x1d8));u32 fresh,repeated;if(!read(0x4e19dc,fresh))return false;
   if(fresh&0x10){if(!row.move(-1,moved)||!read(0x4e19d8,repeated))return false;}else{if(!read(0x4e19d8,repeated))return false;if(repeated&0x10){if(!row.move(-1,moved)||!read(0x4e19d8,repeated))return false;}}
   if(!read(0x4e19dc,fresh))return false;if(((fresh|repeated)&0x20)&&(!row.move(1,moved)||!read(0x4e19d8,repeated)))return false;
   if(!read(0x4e19dc,fresh))return false;if(((fresh|repeated)&0x40)&&(!page.move(-1,moved)||!read(0x4e19d8,repeated)))return false;
   if(!read(0x4e19dc,fresh))return false;if(((fresh|repeated)&0x80)&&!page.move(1,moved))return false;
   if(t.get(0x1dc)!=t.get(0x1d8)&&!call(0x472be0,0,{10}))return false;if(t.get(0x2c)!=t.get(0x28)&&!call(0x472be0,0,{10}))return false;if(!read(0x4e19dc,fresh))return false;
   if(fresh&0x102){if(!call(0x45e900,self,{5})||!call(0x472be0,0,{9}))return false;t.put(0xe000,t.get(0xe000)|4);return true;}
   if(!read(0x4e19dc,fresh))return false;if(fresh&0x80001){const u32 index=t.get(0x1d8)*25+t.get(0x28);if(!t.get(0x5b54+index*4))return true;if(!call(0x45e900,self,{3}))return false;t.put(0x5b4c,t.get(0x1d8)*25+t.get(0x28));if(!row.push()||!call(0x472be0,0,{7}))return false;return confirm(row);}return true;
  }
  if(phase==4){if(signed_word(t.get(0x2b8))<15)return true;t.put(0x2c,t.get(0x28));auto direction=[&](u32 mask,bool& yes){u32 fresh,repeat;if(!read(0x4e19dc,fresh))return false;if(fresh&mask){yes=true;return true;}if(!read(0x4e19d8,repeat))return false;yes=(repeat&mask)!=0;return true;};bool yes;if(!direction(0x10,yes)||(yes&&!row.move(-1,moved))||!direction(0x20,yes)||(yes&&!row.move(1,moved)))return false;if(t.get(0x2c)!=t.get(0x28)&&!call(0x472be0,0,{10}))return false;u32 fresh;if(!read(0x4e19dc,fresh))return false;
   if(fresh&0x102){row.pop();t.put(0x30,25);t.put(0xfc,0);return call(0x45e900,self,{2})&&call(0x472be0,0,{9});}if(fresh&0x80001)return confirm(row);return true;
  }
  if(phase==3){if(t.get(0x2b8)==2){if(!call(0x41af40,0,{0,0,0})||!write(0x4e49a0,returned))return false;const u32 handle=returned;u32 x,y;if(!call(0x484320,0,{handle,7})||!read(0x4c9f70,x)||!read(0x4c9f4c,y)||!call(0x41ce10,0,{x,y}))return false;}
   if(signed_word(t.get(0x2b8))<32||!(t.get(0xe000)&8))return true;u32 fade;if(!call(0x45e880,self,{2})||!read(0x4c9e08,fade)||!call(0x444810,0,{fade}))return false;u32 decoded,day,scene,gear;const u32 owner=t.get(0x5b54+t.get(0x5b4c)*4);if(!read(owner+0x1c,decoded)||!read(decoded+0x88,day)||!write(0x4e4718,day)||!read(decoded+0x8c,scene)||!write(0x4e471c,scene)||!read(decoded+0x90,gear)||!write(0x4e479c,gear)||!write(0x4e47a0,gear)||!write(0x4e4ebc,13)||!write(0x4e46f0,0)||!write(0x4e46f4,0)||!write(0x4e6bac,0x4ddec0+gear*0xac)||!write(0x4e46fc,0)||!call(0x44b7b0,0x4e46f0,{0})||!write(0x4e470c,0xffffffff)||!call(0x4674b0,0,{0}))return false;
   const u32 selected=t.get(0x5b54+t.get(0x5b4c)*4);for(u32 i=0;i<256;++i){u8 ch;if(!h.title_option_read(selected+0x7c+i,&ch,1)||!h.title_option_write(0x4e6a60+i,&ch,1))return false;if(!ch)return write(0x4e6bc0,t.get(0x5b4c))&&write(0x4e6bb0,2);}return false;
  }
  if(phase==5){if(signed_word(t.get(0x2b8))<6||!(t.get(0xe000)&8))return true;for(u32 i=0;i<100;++i){const u32 owner=t.get(0x5b54+i*4);if(owner&&(!call(0x4545d0,owner,{})||!call(0x48a6e8,0,{owner})))return false;}std::memset(t.data+0x5b54,0,0x190);if(!call(0x484320,0,{t.get(0x418),1}))return false;t.put(0x418,0);if(!call(0x484320,0,{t.get(0x73c),1}))return false;t.put(0x73c,0);if(!call(0x45e880,self,{1}))return false;row.pop();}return true;
 }
};
}
bool advance_title_replay_control_v2(AnmView t,u32 self,TitleOptionControlHost& h,u32& result,bool outer_clock){if(!t.data||t.get(0x1c)!=7)return false;ReplayControl c{t,self,h};if(!c.body())return false;if(!outer_clock){result=1;return true;}const u32 old=t.get(0x2b8),token=t.get(0x2c0);t.put(0x2b4,old);float rate=1;if(token&&!h.timer_rate(token,rate))return false;const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=t.floating(0x2bc)+(unit?1.f:rate);t.put(0x2b8,unit?old+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);t.put(0x2bc,word(value));result=1;return true;}
}
