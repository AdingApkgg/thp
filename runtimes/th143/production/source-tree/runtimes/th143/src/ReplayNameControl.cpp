#include "ReplayNameControl.hpp"
#include "MenuCursor.hpp"
#include <cstdio>
namespace th143 {
bool control_replay_name(AnmView m,u32 self,u32 return_substate,ReplayNameControlHost& h){
 if(!m.data||m.get(0x1f0)>12)return false;auto read=[&](u32 p,u32& v){return h.replay_menu_read(p,&v,4);};u32 returned=0;auto call=[&](u32 e,u32 owner,std::initializer_list<u32> args){return h.replay_menu_call(e,owner,args,returned);};auto direction=[&](u32 mask,bool& yes){u32 fresh,repeat;if(!read(0x4e19dc,fresh))return false;if(fresh&mask){yes=true;return true;}if(!read(0x4e19d8,repeat))return false;yes=(repeat&mask)!=0;return true;};MenuCursor cursor{m.sub(0x110)};m.put(0x114,m.get(0x110));i32 ignored;bool yes;
 if(!direction(0x10,yes)||(yes&&!cursor.move(-13,ignored))||!direction(0x20,yes)||(yes&&!cursor.move(13,ignored)))return false;if(!direction(0x40,yes))return false;if(yes&&!cursor.move(signed_word(m.get(0x110))%13?-1:12,ignored))return false;if(!direction(0x80,yes))return false;if(yes&&!cursor.move(signed_word(m.get(0x110))%13==12?-12:1,ignored))return false;if(m.get(0x114)!=m.get(0x110)&&!call(0x472be0,0,{10}))return false;u32 fresh;if(!read(0x4e19dc,fresh))return false;
 if(fresh&0x80001){const u32 selected=m.get(0x110);u8 ch=0;if(selected<88){if(!h.replay_menu_read(0x4c65f0+selected,&ch,1))return false;}else if(selected==88)ch=' ';
  if(selected<=88){const u32 length=m.get(0x1f0);if(length<12){m.data[0x2cc+length]=ch;m.put(0x1f0,length+1);if(m.get(0x1f0)>=12&&!cursor.select(90))return false;}else m.data[0x2cb+length]=ch;if(!call(0x472be0,0,{7}))return false;}
  else if(selected==89){const u32 length=m.get(0x1f0);if(!length)return true;m.put(0x1f0,length-1);m.data[0x2cc+length-1]=' ';return call(0x472be0,0,{9});}
  else if(selected==90){if(!call(0x472be0,0,{17}))return false;char filename[64];const i32 bytes=std::snprintf(filename,sizeof filename,"th143_%.2d.rpy",signed_word(m.get(0x38)+1));if(bytes<0||u32(bytes)>=sizeof filename)return false;const auto* name=reinterpret_cast<const u8*>(filename);const u32 old=m.get(0x204+m.get(0x38)*4);if(old&&(!call(0x4545d0,old,{})||!call(0x48a6e8,0,{old})))return false;if(!h.replay_name_write(name,u32(bytes)+1,self+0x2cc))return false;const u32 slot=m.get(0x38);u32 loaded;if(!h.replay_name_load(name,u32(bytes)+1,loaded))return false;m.put(0x204+slot*4,loaded);if(!call(0x447630,self,{return_substate}))return false;u32 save;if(!read(0x4e6b9c,save))return false;for(u32 i=0;i<13;++i){const u8 value=m.data[0x2cc+i];if(!h.replay_menu_write(save+0xef54+i,&value,1))return false;if(!value)return true;}return false;}
  else if(!call(0x472be0,0,{7}))return false;
 }
 if(!read(0x4e19dc,fresh))return false;if(fresh&0x102){if(!call(0x472be0,0,{9}))return false;const u32 length=m.get(0x1f0);if(!length)return call(0x447630,self,{return_substate});m.put(0x1f0,length-1);m.data[0x2cc+length-1]=' ';}return true;
}
}
