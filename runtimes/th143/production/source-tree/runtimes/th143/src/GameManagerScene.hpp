#pragma once
#include "GameManagerInit.hpp"
#include "PlayerState.hpp"

namespace th143 {
struct GameManagerSceneGlobals {
    u32 new_game=0,scene=1;
    std::array<u32,40> game_state{};
    // 4e1a64..4e1c03 includes the untouched gap and reserved word.
    std::array<u8,0x1a0> keyboard{};
};
struct GameManagerSceneHost:GameManagerMemory {
    virtual bool allocate_scene_history(u32 bytes,u32& token)=0;
};
// 4554b0 with the actual keyboard reset4556f0 and replay position453f40.
// Replay file loading and checkpoint selection precede this operation.
bool begin_game_manager_scene(GameManagerState&,u32 self,PlayerState&,
                              GameManagerSceneGlobals&,GameManagerSceneHost&);
}
