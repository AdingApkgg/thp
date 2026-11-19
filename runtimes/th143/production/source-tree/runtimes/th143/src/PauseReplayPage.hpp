#pragma once
#include "ReplaySaveControl.hpp"
namespace th143 {
struct PauseReplayPageHost:ReplaySaveControlHost {
 virtual bool pause_replay_load(const u8* filename,u32 bytes,u32& result)=0;
 virtual bool pause_replay_select(u32 return_count,u32& result)=0;
 virtual bool pause_replay_name(u32 return_substate)=0;
};
// Full4486c0 substates8..10. Actual4492a0/4494d0 and454800 are supplied by
// their separately gated adapters; the enclosing callback owns timer ticks.
bool advance_pause_replay_page(AnmView menu,u32 self,PauseReplayPageHost&);
}
