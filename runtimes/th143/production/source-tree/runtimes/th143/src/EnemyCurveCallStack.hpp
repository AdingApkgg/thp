#pragma once
#include "AnmState.hpp"
namespace th143 {
// The normal scheduler's aligned, equal callback entry stack aliases the
// animation CALL return slot with class2 contact's untouched local Z word.
void enemy_curve_stack_lookup(u32& word,bool direct);
}
