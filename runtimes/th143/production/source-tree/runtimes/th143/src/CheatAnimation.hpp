#pragma once
#include "AnmOverlay.hpp"
#include "AnmSignal.hpp"
namespace th143 {
// 484c00, first matching child (the original ignores its trailing argument).
AnmView find_animation_child(AnmWorld&,AnmView parent,i32 script);
bool create_cheat_animation(AnmView owner,u32 index,AnmWorld&,AnmOverlay&); //436670
bool clear_cheat_animation(AnmView owner,u32 index,AnmWorld&,AnmSignalHost* callbacks=nullptr); //4366b0
bool signal_cheat_child(AnmView owner,u32 index,i32 child_script,i32 signal,
                        AnmWorld&,AnmSignalHost* callbacks=nullptr); //436700
}
