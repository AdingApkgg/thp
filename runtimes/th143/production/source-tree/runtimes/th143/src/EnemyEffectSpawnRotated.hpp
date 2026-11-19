#pragma once
#include "AnmResourceWorld.hpp"
namespace th143 {
// Prototype ECL315 composition; requires independent original scene replay.
bool spawn_rotated_enemy_effect(AnmResourceWorld&,u32 resource,i32 script,AnmView actor,Vm&,VmHost&,u32& handle);
}
