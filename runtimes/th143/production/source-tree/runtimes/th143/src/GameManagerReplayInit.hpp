#pragma once
#include "GameManagerInit.hpp"
namespace th143 {
struct GameManagerReplayInitHost:GameManagerInitHost {
 virtual bool load_manager_replay(u32 name,u32& status)=0;
};
// Full454080 modes1/2 and inert unsupported modes. Mode0 has its own gated
// initializer. Successful mode1 requires live Root and decoded checkpoint.
bool initialize_game_manager_replay(GameManagerState&,u32 self,u32 mode,u32 name,GameManagerReplayInitHost&,u32& result);
}
