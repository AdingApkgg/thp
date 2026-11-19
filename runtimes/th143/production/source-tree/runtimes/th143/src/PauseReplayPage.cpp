#include "PauseReplayPage.hpp"
#include "MenuCursor.hpp"
#include <cstdio>
namespace th143 {
bool advance_pause_replay_page(AnmView m,u32 self,PauseReplayPageHost& h){
 if(!m.data)return false;u32 returned=0;auto call=[&](u32 entry,u32 owner,std::initializer_list<u32> args){return h.replay_menu_call(entry,owner,args,returned);};MenuCursor row{m.sub(0x38)};const u32 sub=m.get(0x3ec);const i32 clock=signed_word(m.get(0x14));
 if(sub==8){if(clock<20)return true;if(!call(0x447630,self,{9})||!call(0x484730,self+0x1e8,{})||!row.push())return false;m.put(0x40,25);m.put(0x108,1);if(!row.select(0))return false;for(u32 i=1;i<=25;++i){char filename[64];const i32 n=std::snprintf(filename,sizeof filename,"th143_%.2d.rpy",signed_word(i));u32 token;if(n<0||u32(n)>=sizeof filename||!h.pause_replay_load(reinterpret_cast<const u8*>(filename),u32(n)+1,token))return false;m.put(0x204+(i-1)*4,token);}return true;}
 if(sub==9){if(clock<10)return true;u32 result;if(!h.pause_replay_select(6,result))return false;if(result==1)return call(0x447630,self,{10});if(result==2)return call(0x447630,self,{7})&&row.select(1)&&row.push()&&row.select(0);return true;}
 if(sub==10)return clock<10||h.pause_replay_name(9);return false;
}
}
