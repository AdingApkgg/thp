#include "GameManagerInit.hpp"

namespace th143 {
bool initialize_game_manager_recording(GameManagerState& state,u32 self,GameManagerInitGlobals& g,GameManagerInitHost& host){
    auto s=state.view();s.put(0x10,0);g.current=self;
    if(!game_history_clear(state,self,host))return false;
    u32 history;if(!host.allocate_manager_storage(GameManagerState::history_bytes,history)||!game_history_append(state,self,history,host))return false;
    s.put(0x34,history+0x18a4);
    u32 file;if(!host.allocate_manager_storage(0x24,file))return false;
    std::array<u8,0x24> file_bytes{};AnmView f{file_bytes.data()};f.put(0,0x33343174);file_bytes[4]=1;f.put(0x10,0x100);
    if(!host.write_manager_memory(file,file_bytes.data(),file_bytes.size()))return false;s.put(0x18,file);
    u32 header;if(!host.allocate_manager_storage(0xa8,header))return false;
    std::array<u8,0xa8> header_bytes{};AnmView h{header_bytes.data()};
    if(!host.write_manager_memory(header,header_bytes.data(),header_bytes.size()))return false;s.put(0x1c,header);
    u32 checkpoint;if(!host.allocate_manager_storage(0x10c,checkpoint))return false;
    std::array<u8,0x10c> checkpoint_bytes{};AnmView c{checkpoint_bytes.data()};
    if(!host.write_manager_memory(checkpoint,checkpoint_bytes.data(),checkpoint_bytes.size()))return false;s.put(0x20,checkpoint);
    header_bytes[0x11]=u8(((g.game_flags>>5)&1)|((g.game_flags&0x60)==0x40?2:0));
    for(auto pair:{std::pair<u32,u32>{0x84,7},{0x94,15},{0x98,16},{0x9c,14},{0xa0,12},{0xa4,13},{0x88,10},{0x8c,11}})h.put(pair.first,g.game_state[pair.second]);
    h.put(0x90,g.scene);if(g.root_present)std::memcpy(header_bytes.data()+0x20,g.root_snapshot.data(),0x5c);
    if(!host.write_manager_memory(header,header_bytes.data(),header_bytes.size()))return false;
    c.put(0,u32(u16(g.scene))|u32(g.random.seed)<<16);g.random.calls=0;
    c.put(0x108,g.new_game&1);std::memcpy(checkpoint_bytes.data()+0x14,g.game_state.data(),0xa0);
    for(u32 i=0;i<20;++i)c.put(0xb8+i*4,i*0xdeaddeadu);
    if(!host.write_manager_memory(checkpoint,checkpoint_bytes.data(),checkpoint_bytes.size()))return false;
    for(auto item:{std::array<u32,4>{0x455420,16,0,8},{0x455440,35,0,0x70},{0x455490,68,1,12}}){u32 callback;
        if(!host.register_manager_callback(item[0],i32(item[1]),item[2]!=0,self,callback))return false;s.put(item[3],callback);
    }s.put(0x74,g.scene);s.put(0x6c,0xffffffff);return true;
}
}
