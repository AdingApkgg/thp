#pragma once
#include "ReplayListDraw.hpp"
namespace th143 {
struct ReplaySaveDrawHost:ReplayListDrawHost {
 virtual bool replay_name_cursor(AnmView menu,const std::array<float,3>& position)=0;
};
// Actual449890. Current replay, CRT time and name cursor retain ownership.
bool draw_replay_save(AnmView menu,AnmView ascii,u32 current_replay,ReplaySaveDrawHost&);
}
