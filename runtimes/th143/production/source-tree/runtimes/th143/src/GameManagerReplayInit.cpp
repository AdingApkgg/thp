#include "GameManagerReplayInit.hpp"
#include "ApplicationGameRequests.hpp"
namespace th143 {
bool initialize_game_manager_replay(GameManagerState& state,u32 self,u32 mode,u32 name,GameManagerReplayInitHost& h,u32& result){
 if(!mode)return false;auto s=state.view();s.put(0x10,mode);result=0;auto read=[&](u32 p,u32& v){return h.read_manager_memory(p,&v,4);};auto write=[&](u32 p,u32 v){return h.write_manager_memory(p,&v,4);};
 if(mode!=1){if(mode==2){u32 status;if(!h.load_manager_replay(name,status))return false;if(status)result=0xffffffff;}return true;}
 if(!write(0x4e6b98,self))return false;u32 status;if(!h.load_manager_replay(name,status))return false;if(status){result=0xffffffff;return true;}
 u32 root;if(!read(0x4e6a5c,root)||!root)return false;std::array<u8,0x5c> root_snapshot;if(!h.read_manager_memory(s.get(0x1c)+0x20,root_snapshot.data(),root_snapshot.size())||!h.write_manager_memory(root+0x24,root_snapshot.data(),root_snapshot.size()))return false;
 const u32 checkpoint=s.get(0x4c);s.put(0x40,s.get(0x3c));s.put(0x48,s.get(0x44));s.put(0x50,0xffffffff);
 for(auto item:{std::pair<u32,u32>{0x94,0x4e4710},{0x98,0x4e4714},{0x9c,0x4e4728},{0xa0,0x4e4720},{0xa4,0x4e4724}}){u32 value;if(!read(s.get(0x1c)+item.first,value)||!write(item.second,value))return false;}
 u16 seed;if(!h.read_manager_memory(checkpoint+2,&seed,2)||!h.write_manager_memory(0x4e69e8,&seed,2)||!write(0x4e69ec,0))return false;std::array<u8,0xa0> game;if(!h.read_manager_memory(checkpoint+0x14,game.data(),game.size())||!h.write_manager_memory(0x4e46f0,game.data(),game.size()))return false;
 std::array<u8,0xc4> configured;if(!h.read_manager_memory(0x4e46f0,configured.data(),configured.size()))return false;AnmView view{configured.data()};u32 ignored;if(!initialize_application_game_mode(view,signed_word(view.get(0x1c))<0?0:2,ignored)||!write(0x4e470c,view.get(0x1c))||!write(0x4e47b0,view.get(0xc0)))return false;
 for(auto item:{std::array<u32,4>{0x455430,16,0,8},{0x455440,35,0,0x70},{0x455490,68,1,12}}){u32 token;if(!h.register_manager_callback(item[0],i32(item[1]),item[2]!=0,self,token))return false;s.put(item[3],token);}s.put(0x74,0xffffffff);return true;
}
}
