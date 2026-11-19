#pragma once
#include "GameManagerState.hpp"
#include "Rng.hpp"

namespace th143 {
struct GameManagerInitGlobals {
    u32 current=0,game_flags=0,new_game=0,scene=1;
    std::array<u32,40> game_state{}; //4e46f0..4e478f
    Rng random;
    bool root_present=false;
    std::array<u32,23> root_snapshot{}; //Root+24
};
struct GameManagerInitHost:GameManagerMemory {
    virtual bool allocate_manager_storage(u32 bytes,u32& token)=0;
    virtual bool register_manager_callback(u32 entry,i32 priority,bool draw,u32 owner,u32& token)=0;
};
// Mode0 portion of454080, composed with455bb0/455a70. Replay loading remains
// a separate path; recording headers/checkpoints are constructed here.
bool initialize_game_manager_recording(GameManagerState&,u32 self,GameManagerInitGlobals&,GameManagerInitHost&);
}
