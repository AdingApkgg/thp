#pragma once
#include "GameRenderRuntime.hpp"
namespace th143 {
//446290 and4481d0. Pending independent screenshot capture (4116e0 bits0/1)
// needs its own surface-copy services and is rejected here. The menu's two
// embedded VMs are actual draws into the existing application render target.
bool finish_game_application_draw(GameRenderRuntime&,GameRenderDevice&,AnmView menu,u32 independent_signals);
}
