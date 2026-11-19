#pragma once
#include "AnmState.hpp"
#include <array>

namespace th143 {
struct GameManagerState {
    static constexpr u32 bytes=0x17c,history_bytes=0x18b4;
    std::array<u8,bytes> data{};
    AnmView view(){return {data.data()};}
    void construct(){data.fill(0);}
};
struct GameManagerMemory {
    virtual ~GameManagerMemory()=default;
    virtual bool read_manager_memory(u32,void*,u32)=0;
    virtual bool write_manager_memory(u32,const void*,u32)=0;
    virtual bool release_manager_storage(u32)=0;
    virtual bool remove_manager_callback(u32)=0;
};
// 455a70: the host supplies a newly allocated history_bytes block, while
// construction and list ownership are computed here.
bool game_history_append(GameManagerState&,u32 self,u32 block,GameManagerMemory&);
// 455bb0 and4545d0. Freed storage can remain readable in an audit host.
bool game_history_clear(GameManagerState&,u32 self,GameManagerMemory&);
bool game_manager_cleanup(GameManagerState&,u32 self,u32& current,GameManagerMemory&);
}
