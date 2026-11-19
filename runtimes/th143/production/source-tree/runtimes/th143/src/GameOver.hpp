#pragma once
#include "GameClock.hpp"
#include "PauseMenu.hpp"
#include "SaveData.hpp"
#include "AnmOverlay.hpp"

namespace th143 {
struct GameOverGlobals {
    u32 root_mode=0,root_flags=0,config=0x180,game_flags=0,application_state=0;
    u32 text_resource=0,front_resource=0,presentation=0;
    float rate=1;
    double statistics_time=0;
    GameClock clock;
};
struct GameOverHost:SaveDataHost,GameClockHost {
    virtual bool pause_audio()=0;
    virtual bool sound_and_flush(u32 id)=0;
};
bool game_statistics_time(SaveData&,GameOverGlobals&,GameOverHost&);
// 449990. Owns the failure entry, with the menu/graphics/save owners supplied
// by their normal constructors. Navigation and process startup are separate.
bool game_over(PauseMenu&,SaveData&,GameOverGlobals&,AnmWorld&,AnmOverlay&,u32 reason,GameOverHost&);
}
