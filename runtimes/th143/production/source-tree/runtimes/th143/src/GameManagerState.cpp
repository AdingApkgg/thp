#include "GameManagerState.hpp"

namespace th143 {
namespace {
struct Memory {
    GameManagerState& state;u32 self;GameManagerMemory& host;
    bool read(u32 token,u32& value){
        if(token>=self&&std::uint64_t(token)+4<=std::uint64_t(self)+state.data.size()){value=state.view().get(token-self);return true;}
        return host.read_manager_memory(token,&value,4);
    }
    bool write(u32 token,u32 value){
        if(token>=self&&std::uint64_t(token)+4<=std::uint64_t(self)+state.data.size()){state.view().put(token-self,value);return true;}
        return host.write_manager_memory(token,&value,4);
    }
    bool unlink(u32 next,u32 previous){return (!next||write(next+8,previous))&&(!previous||write(previous+4,next));}
};
}
bool game_history_append(GameManagerState& state,u32 self,u32 block,GameManagerMemory& host){
    if(!block)return false;std::array<u8,GameManagerState::history_bytes> data{};AnmView b{data.data()};
    b.put(0x1518,block);b.put(0x18a0,block+0x151c);b.put(0x18a4,block);
    if(!host.write_manager_memory(block,data.data(),data.size()))return false;
    Memory memory{state,self,host};u32 previous=self+0x24,next=0,budget=100000;
    while(true){if(!budget--||!memory.read(previous+4,next))return false;if(!next)break;previous=next;}
    const u32 node=block+0x18a4;u32 tail;
    if(!memory.read(previous+12,tail))return false;
    if(tail&&!memory.write(previous+12,node))return false;
    if(!memory.write(previous+4,node)||!memory.write(node+8,previous))return false;
    auto s=state.view();s.put(0x38,s.get(0x38)+1);return true;
}
bool game_history_clear(GameManagerState& state,u32 self,GameManagerMemory& host){
    Memory memory{state,self,host};u32 node=state.view().get(0x28),budget=100000;
    while(node){
        u32 block,next;if(!budget--||!memory.read(node,block)||!memory.read(node+4,next))return false;
        if(block){
            u32 following,previous;
            if(!memory.read(block+0x18a8,following)||!memory.read(block+0x18ac,previous)||!memory.unlink(following,previous)||
               !memory.write(block+0x18a8,0)||!memory.write(block+0x18ac,0)||!host.release_manager_storage(block))return false;
        }node=next;
    }return true;
}
bool game_manager_cleanup(GameManagerState& state,u32 self,u32& current,GameManagerMemory& host){
    auto s=state.view();
    // Unlike most owner fields, these three calls include free(NULL).
    if(!host.release_manager_storage(s.get(0x18))||!game_history_clear(state,self,host)||!host.release_manager_storage(s.get(0x1c)))return false;
    s.put(0x1c,0);if(!host.release_manager_storage(s.get(0x20)))return false;s.put(0x20,0);
    for(u32 at:{8,0x70,12})if(s.get(at)&&!host.remove_manager_callback(s.get(at)))return false;
    if(current==self)current=0;
    Memory memory{state,self,host};if(!memory.unlink(s.get(0x58),s.get(0x5c)))return false;
    s.put(0x5c,0);s.put(0x58,0);return true;
}
}
