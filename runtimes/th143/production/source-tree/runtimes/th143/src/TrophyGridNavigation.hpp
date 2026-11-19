#pragma once
#include "MenuCursor.hpp"
namespace th143 {
//Full465998..465b2b within465890 phase1. Seventy slots, lastrow60..69 skips
//locked flags atSaveeff9+index. A selectedlastrow requires one unlockedcell.
//Text refresh, rewards/notices, hidden keyboard sequence and outerclock follow.
bool navigate_trophy_grid(AnmView title,AnmView save,u32 fresh,u32 repeated);
}
