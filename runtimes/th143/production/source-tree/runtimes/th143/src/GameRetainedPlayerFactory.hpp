#pragma once
#include "GameOwnerRuntime.hpp"
namespace th143 {
//44ca60/44bd00 branch that consumes4e6b8c. The existing relocated/mutable
// SHT allocation remains owned by the session; no file is read or reparsed.
bool create_player_with_retained_shots(GameOwnerRuntime&,GameFrameRuntime&,AnmWorld&,
    GameOwnerServices&,u32& cached_shots,GameManagerInitGlobals&,u32& result);
}
