#pragma once
#include "EclVm.hpp"
#include <array>

namespace th143 {
// Original4ddec0:76 records, including the legacy debug entry at index0.
// The remaining words preserve original signed/float bit patterns unchanged.
struct SceneDescriptor {
    u32 id;
    const char *stage,*ecl,*music,*message,*animation;
    std::array<u32,37> parameters;
};
const SceneDescriptor* scene_descriptor(u32 id);
const SceneDescriptor* gameplay_scene(u32 id);
const SceneDescriptor* scene_for_day(u32 day,u32 within_day);
}
