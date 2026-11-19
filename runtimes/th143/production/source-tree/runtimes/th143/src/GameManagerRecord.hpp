#pragma once
#include "GameManagerScene.hpp"
namespace th143 {
struct GameManagerRecordGlobals {
    std::array<u8,0x1a0> keyboard{}; //4e1a64..4e1c03
    bool root_present=false;
    u32 root_flags=0,dialog=0,raw_keys=0,focus_flags=0;
    float stage_value=0;
};
void update_record_input(std::array<u8,0x1a0>&); //41a750
// 4548b0/455420: original input acquisition, repeat/focus and replay recording.
bool record_game_manager_frame(GameManagerState&,u32 self,GameManagerRecordGlobals&,GameManagerSceneHost&);
// 455440, including the signed modulo-eight replay acceleration condition.
i32 game_manager_replay_control(GameManagerState&,bool root_present,u32 root_flags,u32 raw_keys);
}
