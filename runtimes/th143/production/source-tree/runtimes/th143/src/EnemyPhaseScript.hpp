#pragma once
#include "EclOwner.hpp"
namespace th143 {
// Original41d2b0 followed by41d350. Reset preserves the root stack bytes,
// difficulty and upper flag bits while releasing secondary contexts in order.
void reset_enemy_threads(EclOwner&);
// 420400's two phase paths share reset/lookup. A damage phase executes the
// replacement root immediately; a timer phase waits for the next owner update.
bool restart_enemy_phase(EclOwner&,const char* name,bool execute_now,float elapsed,i32& result);
}
