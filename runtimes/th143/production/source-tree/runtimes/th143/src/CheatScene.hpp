#pragma once
#include "CheatAnimation.hpp"
namespace th143 {
struct CheatSceneGlobals {
    u32 alternate=0,primary=0,secondary=0,scene=0;
    bool menu_present=false;
    u32 menu_state=0;
    u8 unlock=0,scene35_record=0;
    std::array<u32,9> selection{};
};
void construct_cheat_owner(AnmView); //436960, global publication belongs to owner storage.
void set_cheat_state(AnmView,i32 state); //436600
bool position_cheat_scene(AnmView,AnmWorld&); //438380
bool begin_cheat_scene(AnmView,i32 mode,const CheatSceneGlobals&,AnmWorld&,AnmOverlay&); //436c30
bool return_cheat_scene(AnmView); //436eb0
bool end_cheat_scene(AnmView,AnmWorld&,AnmSignalHost* callbacks=nullptr); //436ee0
}
