#pragma once
#include "PlayerState.hpp"
namespace th143 {
struct PlayerClearExitHost {virtual ~PlayerClearExitHost()=default;virtual bool clear_exit_signal(u32 handle,i32 signal)=0;};
//4321b0: begin the clear exit, signal sixteen option visuals, reset clock.
bool begin_player_clear_exit(PlayerState&,PlayerClearExitHost&);
}
