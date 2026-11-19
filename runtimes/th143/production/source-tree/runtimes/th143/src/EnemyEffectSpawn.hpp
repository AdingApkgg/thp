#pragma once
#include "AnmResourceWorld.hpp"
namespace th143 {
// ECL307/4222fd: the effect enters the HEAD of the primary animation list.
bool spawn_enemy_effect(AnmResourceWorld&,u32 resource,i32 script,const std::array<float,3>&,u32& handle);
}
