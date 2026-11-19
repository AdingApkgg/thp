#include "GameManagerReplayFrame.hpp"
namespace th143 {
bool advance_game_manager_replay(GameManagerState& state,std::array<u8,0x1a0>& keyboard,bool root_present,GameManagerReplayFrameHost& h){
 if(!root_present)return true;auto s=state.view();AnmView k{keyboard.data()};auto clear=[&](){k.put(0x184,0);k.put(0x190,0);k.put(0x194,0);};
 if(signed_word(s.get(0x50))<0){clear();return true;}if(signed_word(s.get(0x74))<0){clear();s.put(0x6c,s.get(0x6c)+1);return true;}
 k.put(0x188,k.get(0x184));u32 frames;if(!h.read_manager_memory(s.get(0x4c)+4,&frames,4))return false;
 if(signed_word(s.get(0x50))<signed_word(frames)){u16 held,pressed,released;const u32 pointer=s.get(0x40);if(!h.read_manager_memory(pointer,&held,2)||!h.read_manager_memory(pointer+2,&pressed,2)||!h.read_manager_memory(pointer+4,&released,2))return false;
  if(held==0xffff&&pressed==0xffff&&released==0xffff){clear();return h.end_manager_replay();}k.put(0x184,held);k.put(0x190,pressed);k.put(0x194,released);update_record_input(keyboard);const u32 stage=s.get(0x48);u8 value;if(!h.read_manager_memory(stage,&value,1))return false;s.data[0x68]=value;s.put(0x40,s.get(0x40)+6);
  if(signed_word(s.get(0x6c))%30==0)s.put(0x48,stage+1);
 }else clear();s.put(0x50,s.get(0x50)+1);s.put(0x6c,s.get(0x6c)+1);return true;
}
}
