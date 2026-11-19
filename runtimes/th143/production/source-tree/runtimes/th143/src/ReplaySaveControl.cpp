#include "ReplaySaveControl.hpp"
#include "MenuCursor.hpp"
#include <string>
namespace th143 {
bool control_replay_save_list(AnmView m,u32 self,u32 return_count,ReplaySaveControlHost& h,u32& result){
 if(!m.data)return false;result=0;u32 returned=0;auto read=[&](u32 p,u32& value){return h.replay_menu_read(p,&value,4);};auto call=[&](u32 entry,u32 owner,std::initializer_list<u32> args){return h.replay_menu_call(entry,owner,args,returned);};MenuCursor row{m.sub(0x38)};m.put(0x3c,m.get(0x38));u32 fresh,repeated;if(!read(0x4e19dc,fresh))return false;i32 ignored;
 if(fresh&0x10){if(!row.move(-1,ignored)||!read(0x4e19dc,fresh)||!read(0x4e19d8,repeated))return false;}else{if(!read(0x4e19d8,repeated))return false;if(repeated&0x10){if(!row.move(-1,ignored)||!read(0x4e19dc,fresh)||!read(0x4e19d8,repeated))return false;}}
 if(((fresh|repeated)&0x20)&&(!row.move(1,ignored)||!read(0x4e19dc,fresh)))return false;if(m.get(0x3c)!=m.get(0x38)&&(!call(0x472be0,0,{10})||!read(0x4e19dc,fresh)))return false;
 if(fresh&0x80001){MenuCursor letters{m.sub(0x110)};if(!letters.select(0))return false;m.put(0x118,91);m.put(0x1e0,1);u32 manager,header;if(!read(0x4e6b98,manager)||!read(manager+0x1c,header)||!call(0x48b338,0,{header+0x14}))return false;u32 save;if(!read(0x4e6b9c,save))return false;bool terminated=false;for(u32 i=0;i<13;++i){u8 ch;if(!h.replay_menu_read(save+0xef54+i,&ch,1))return false;m.data[0x2cc+i]=ch;if(!ch){terminated=true;break;}}if(!terminated)return false;m.put(0x1f0,0);std::string blank;for(u32 i=0;i<13;++i){u8 ch;if(!h.replay_menu_read(0x4c65dc+i,&ch,1))return false;if(!ch)break;blank.push_back(char(ch));}const std::string current(reinterpret_cast<const char*>(m.data+0x2cc));if(current!=blank&&!letters.move(-1,ignored))return false;u32 length=12;while(length&&m.data[0x2cc+length-1]==' ')--length;m.put(0x1f0,length);if(!call(0x472be0,0,{7}))return false;result=1;return true;}
 if(fresh&0x102){if(!call(0x4846f0,self+0x1e8,{}))return false;row.pop();m.put(0x40,return_count);m.put(0x108,1);const u16 bits=u16(m.get(0x38)+7);const i32 signal=bits&0x8000?i32(bits)-65536:i32(bits);if(!call(0x484320,0,{m.get(0x1e8),u32(signal)}))return false;for(u32 i=0;i<25;++i){const u32 token=m.get(0x204+i*4);if(token&&(!call(0x4545d0,token,{})||!call(0x48a6e8,0,{token})))return false;m.put(0x204+i*4,0);}if(!call(0x472be0,0,{9}))return false;result=2;}return true;
}
}
