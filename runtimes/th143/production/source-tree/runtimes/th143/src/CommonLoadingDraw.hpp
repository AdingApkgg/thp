#pragma once
#include "AnmResourceWorld.hpp"
namespace th143 {
//4435b0/4436b0: register the sig and ASCII loading visuals once, then count
// presentation passes. Existing nonzero ASCII handles remain authoritative.
bool draw_common_loading(AnmView common,AnmView ascii,AnmResourceWorld&,u32& result);
}
