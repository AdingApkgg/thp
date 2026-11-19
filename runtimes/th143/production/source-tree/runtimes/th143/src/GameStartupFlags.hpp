#pragma once
#include "AnmState.hpp"
namespace th143 {
//4674b0: globalgame+c0 bits800/400; only argument bit0 matters. The original
//EAX is the xor delta for bit400, not the final flags or an object handle.
bool set_application_scene_flags(AnmView game,u32 enabled,u32& result);
}
