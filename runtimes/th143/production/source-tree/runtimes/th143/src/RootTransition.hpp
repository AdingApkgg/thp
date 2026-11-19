#pragma once
#include "AnmWorld.hpp"

namespace th143 {
// 41ce10 uses the ASCII-owned handle as its existence test, even after the
// animation retires. The caller clears that ownership field for a new scene.
bool root_transition(AnmWorld&,u32 ascii_resource,u32& owned_handle,float x=480.f,float y=392.f);
}
