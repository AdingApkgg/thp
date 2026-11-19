#include "TitleMusicEntry.hpp"
#include "MusicRoomComments.hpp"
#include "MenuCursor.hpp"
namespace th143 {
namespace {
void reset(AnmView t,TitleMusicEntryHost& h){const u32 flags=t.get(0x2c4);if(!(flags&1)){t.put(0x2c0,h.global_rate_token());t.put(0x2c4,flags|1);}t.put(0x2b4,0xffffffff);t.put(0x2b8,0);t.put(0x2bc,0);}
bool tick(AnmView t,TitleMusicEntryHost& h){const u32 old=t.get(0x2b8),token=t.get(0x2c0);t.put(0x2b4,old);float rate=1;if(token&&!h.timer_rate(token,rate))return false;const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=t.floating(0x2bc)+(unit?1.f:rate);t.put(0x2b8,unit?old+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);t.put(0x2bc,word(value));return true;}
}
bool advance_title_music_entry(AnmView t,u32 self,TitleMusicEntryHost& h,u32& result){
 if(!t.data||t.get(0x1c)!=6||t.get(0x24)||(t.get(0xe000)&1)||signed_word(t.get(0x2b8))<1)return false;u32 returned=0;
 auto read=[&](u32 p,u32& v){return h.title_music_read(p,&v,4);};auto write=[&](u32 p,u32 v){return h.title_music_write(p,&v,4);};auto call=[&](u32 e,u32 owner,std::initializer_list<u32> a){return h.title_music_call(e,owner,a,returned);};
 auto create=[&](u32 resource,u32 script,u32& handle){
  u32 counter;if(!read(resource+0x134,counter)||!write(resource+0x134,counter+1)||!call(0x484de0,0,{}))return false;const u32 vm=returned;
  if(!call(0x40ab20,resource,{vm,script}))return false;u32 flags;if(!read(vm+0x1c,flags)||!write(vm+0x1c,flags|0x200)||!write(vm+0x59c,0)||!write(vm+0x5a0,0)||!write(vm+0x5a4,0)||!write(vm+0x50,0)||!call(0x474710,vm,{})||!call(0x483a70,0,{vm}))return false;handle=returned;return true;
 };
 if(t.get(0x2b8)==1){
  t.put(0x30,6);if(!MenuCursor{t.sub(0x28)}.select(0))return false;
  if(!t.get(0x73c)){u32 ascii,resource,handle;if(!read(0x4e69f8,ascii)||!read(ascii+0x191e4,resource)||!create(resource,19,handle))return false;t.put(0x73c,handle);}
  if(!call(0x45e970,self,{86}))return false;u32 token,declared;std::vector<u8> backing;if(!h.title_music_file(0x4c7e44,token,declared,backing))return false;t.put(0x5ce4,token);
  if(!token){
   t.put(0x5ce4,0);for(u32 i=0;signed_word(i)<signed_word(t.get(0x7f4));++i)if(!call(0x484320,0,{t.get(0x780+i*4),1}))return false;
   for(u32 i=0;i<8;++i)if(!call(0x484320,0,{t.get(0x7d0+i*4),1}))return false;if(!call(0x472be0,0,{9}))return false;t.put(0x24,3);reset(t,h);result=1;return tick(t,h);
  }
  u32 records;if(!parse_music_room_comments(t,declared,backing,records)||!h.title_music_write(token,backing.data(),backing.size()))return false;t.put(0x30,records);if(!MenuCursor{t.sub(0x28)}.select(0))return false;t.put(0x5a44,0);t.put(0x7f4,records);
  for(u32 i=0;i<8;++i){u32 resource,handle;if(!read(0x4e4eec,resource)||!create(resource,19+i,handle))return false;t.put(0x7d0+i*4,handle);}t.put(0x7f8,0);t.put(0x7fc,0);t.put(0x800,0);
 }
 if(signed_word(t.get(0x2b8))<10){
  u32 a,b,c,d,e;double indent;if(!read(0x4c9ef0,a)||!read(0x4c9ee0,b)||!read(0x4c9e94,c)||!read(0x4c9e08,d)||!read(0x4c9eb8,e)||!h.title_music_read(0x4c9e30,&indent,8))return false;
  float x=real(a),product=float(signed_word(t.get(0x5a44)))*real(c),y=real(b)-product;y+=float(signed_word(t.get(0x2b8)*40-40));y*=real(d);
  for(u32 i=t.get(0x2b8)*2-2;signed_word(i)<signed_word(t.get(0x2b8)*2);++i){
   if(signed_word(i)>=signed_word(t.get(0x7f4)))break;u32 handle;if(!create(t.get(0x14),i+186,handle))return false;t.put(0x780+i*4,handle);u32 pool;if(!read(0x538de8,pool)||!call(0x484280,pool,{handle}))return false;const u32 vm=returned;if(!vm){t.put(0x780+i*4,0);return false;}
   u32 save;u8 heard;if(!read(0x4e6b9c,save)||!h.title_music_read(save+0xef74+i,&heard,1)||!read(0x538de8,pool))return false;
   if(heard){if(!call(0x482c20,0,{pool,vm,0xffffff,0,0,0,0,self+0x1004+i*0x42}))return false;}
   else if(!call(0x482c20,0,{pool,vm,0xffffff,0,0,0,0,0x4c7e54,i+1}))return false;
   u32 flags;if(!read(vm+0x18,flags))return false;const i32 first=signed_word(t.get(0x5a44));const bool visible=signed_word(i)>=first&&signed_word(i)<first+10;if(!write(vm+0x18,visible?flags|2:flags&~2u))return false;
   if(i==t.get(0x28))x=float(double(x)-indent);if(!call(0x418300,vm,{4,0,vm+0x3c,word(x),word(y),0}))return false;if(i==t.get(0x28))x=float(double(x)+indent);
   const u32 signal=i==t.get(0x28)?2u:3u;y+=real(e);u32 callback;if(!read(vm+0x5c4,callback))return false;if(callback&&!call(callback,vm,{signal}))return false;if(!write(vm+0x4a0,signal))return false;
  }
 }
 if(signed_word(t.get(0x2b8))>=10){t.put(0x24,1);reset(t,h);}result=1;return tick(t,h);
}
}
