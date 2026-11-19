#pragma once
#include "AnmState.hpp"
#include <initializer_list>
namespace th143 {
struct GameReplayEndEntryHost {
 virtual ~GameReplayEndEntryHost()=default;
 virtual bool replay_end_read(u32,void*,u32)=0;
 virtual bool replay_end_write(u32,const void*,u32)=0;
 virtual bool replay_end_call(u32 entry,u32 owner,std::initializer_list<u32>,u32& result)=0;
};
// Full448490;483f00 output handles are normalized to scalar results. The
// caller supplies the entry-cached Menu owner; Root/HUD/globals remain fresh.
bool enter_game_replay_end(AnmView menu,GameReplayEndEntryHost&,u32& result);
}
