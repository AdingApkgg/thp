#pragma once
#include "CheatScene.hpp"
#include "MenuCursor.hpp"
namespace th143 {
struct CheatControllerGlobals {
    u32 fresh=0,repeated=0,primary=0,secondary=0,saved_primary=0,saved_secondary=0;
    u32 menu_token=0,menu_animation=0,primary_count=0,secondary_count=0,secondary_enabled=0;
    u8 unlock=0;
};
struct CheatControllerHost {
    virtual ~CheatControllerHost()=default;
    virtual bool cheat_item_level(u32 id,bool notify)=0; //456620
    virtual bool cheat_persist()=0; //4562e0
    virtual bool cheat_sound(u32 id)=0; //472be0
};
// Original436f70, all six active states and the always-executed owner timer.
bool update_cheat_controller(AnmView,CheatControllerGlobals&,AnmWorld&,AnmOverlay&,CheatControllerHost&);
}
