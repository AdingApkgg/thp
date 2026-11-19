#pragma once
#include "AnmVm.hpp"

namespace th143 {
// Original473ca0 + final4822e0 template loop. Builds from a zero constructed
// VM and script/resource metadata, then executes only negative-time commands.
// The host owns resource bytes, descriptors and RNG, never native VM results.
bool anm_template(AnmView, u32 self_token, u32 resource, i32 script, AnmVmHost&);
}
