#pragma once
#include "AnmWorld.hpp"

namespace th143 {
// Original483f00 general instance factory and483830 secondary-list update.
// The regular primary update follows this pass and shares its visit counter.
struct AnmOverlay {
    std::array<u32,7> draws{};
    bool create(AnmWorld&,u32 resource,i32 script,const std::array<float,3>* position,
                float rotation,i32 layer,u32 flags,u32& handle);
    bool update(AnmWorld&);
};
}
