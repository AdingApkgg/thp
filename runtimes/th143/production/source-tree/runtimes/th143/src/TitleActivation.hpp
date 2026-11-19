#pragma once
#include "TitleLoad.hpp"
#include "TitleMainIntro.hpp"
#include "MusicScene.hpp"
namespace th143 {
struct TitleActivationGlobals {
    u32 return_mode=0,trophy_owner=0,fade_handle=0,startup_flags=0,game_state=0,cached_game_state=0;
};
struct TitleActivationBindings {
    GameTitleRuntime& title;GameCheatRuntime& cheat;GameAsciiRuntime& ascii;
    GameFrameRuntime& frames;AnmResourceWorld& world;SaveData& save;AnmView application,audio;
    TitleActivationGlobals& globals;
};
//45f6e0 cold state0 and music prefix, followed by the main-page intro.
// Active fade/trophy overlays, pending39 and return modes other than0 reject.
bool advance_title_activation(TitleActivationBindings&,u32& result);
}
