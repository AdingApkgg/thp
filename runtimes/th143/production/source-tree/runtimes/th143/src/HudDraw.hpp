#pragma once
#include "AnmWorld.hpp"
#include "AsciiFormat.hpp"
#include "CheatAnimation.hpp"
namespace th143 {
struct HudDrawGlobals {u32 high_score=0,high_score_scene=0,scene=0;};
//42e6c0: score/time/countdown text generation over the actual HUD and ASCII
// owners. A missing required VM fails; no visibility or queue path is omitted.
bool draw_hud_text(AnmView hud,AnmView ascii,AnmView enemy,AnmView special,const HudDrawGlobals&,AnmWorld&);
}
