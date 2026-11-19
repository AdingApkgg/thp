#pragma once
#include "AnmState.hpp"
namespace th143 {
//40c6e0: decrement lifetimes and compact surviving138-byte records in place.
// Old source/tail bytes survive; callers must not clear unused queue slots.
bool age_ascii_entries(AnmView owner);
//40b590: queue update followed by the191e0 frame counter increment.
bool advance_ascii_frame(AnmView owner);
}
