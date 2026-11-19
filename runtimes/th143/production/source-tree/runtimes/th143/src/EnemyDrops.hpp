#pragma once
#include "AnmState.hpp"
#include "Rng.hpp"
#include "ItemPool.hpp"
namespace th143 {
// Original41d740, a0x48-byte drop descriptor followed by the caller position.
// Counts1..14 share the game RNG; only types13/14 create delayed items here.
// The caller separately handles descriptor word0 before calling this routine.
bool enemy_drops(AnmView descriptor,const std::array<float,3>& position,Rng&,ItemPool&,u32 rate_token=0x4e40b0);
}
