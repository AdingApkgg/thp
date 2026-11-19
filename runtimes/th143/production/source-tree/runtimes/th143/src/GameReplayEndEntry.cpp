#include "GameReplayEndEntry.hpp"
namespace th143 {
bool enter_game_replay_end(AnmView m,GameReplayEndEntryHost& h,u32& result){
 if(!m.data)return false;auto read=[&](u32 p,u32& v){return h.replay_end_read(p,&v,4);};auto write=[&](u32 p,u32 v){return h.replay_end_write(p,&v,4);};u32 returned=0;auto call=[&](u32 e,u32 owner,std::initializer_list<u32> args){return h.replay_end_call(e,owner,args,returned);};auto timer=[&](u32 at){if(!(m.get(at+16)&1)){m.put(at+12,0x4e40b0);m.put(at+16,m.get(at+16)|1);}m.put(at,0xffffffff);m.put(at+4,0);m.put(at+8,0);};
 m.put(0x3e8,m.get(0x3e4));m.put(0x3e4,1);m.put(0x3ec,0);timer(0x10);m.put(0x3ec,2);timer(0x10);timer(0x24);u32 root,flags;if(!read(0x4e6a5c,root)||!read(root+0x80,flags))return false;m.put(0x10c,0);if(!write(root+0x80,flags|0x10))return false;m.put(0x91bc,m.get(0x91bc)|1);u32 resource;if(!read(0x4e4eec,resource)||!call(0x483f00,resource,{58,0,0,0xffffffff,4,0}))return false;m.put(0x1ec,returned);
 u32 hud;if(!read(0x4e6a54,hud)||!read(hud+0x2ac,resource))return false;m.put(0x91c0,resource);if(!call(0x483f00,resource,{106,0,0,0xffffffff,4,0}))return false;m.put(0x1e8,returned);if(!call(0x484320,0,{returned,3})||!call(0x433f70,0,{}))return false;u32 rate,presentation;if(!read(0x4e40b0,rate))return false;m.put(0x2d8,rate);if(!write(0x4e40b0,0x3f800000)||!read(0x53b150,presentation))return false;m.put(0x200,presentation);if(!write(0x53b150,0))return false;result=presentation;return true;
}
}
