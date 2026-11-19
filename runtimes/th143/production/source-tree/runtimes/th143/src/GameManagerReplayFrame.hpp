#pragma once
#include "GameManagerRecord.hpp"
namespace th143 {
struct GameManagerReplayFrameHost:GameManagerMemory {virtual bool end_manager_replay()=0;};
// Full455430/4549a0. The input counters execute the same41a750 body as the
// recording owner;448490 replay-end handling is an explicit service.
bool advance_game_manager_replay(GameManagerState&,std::array<u8,0x1a0>& keyboard,bool root_present,GameManagerReplayFrameHost&);
}
