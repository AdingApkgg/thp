#pragma once
#include "EnemyCleanup.hpp"

namespace th143 {
struct ResourceCleanupMemory:EnemyCleanupMemory {
    // COM Release is a graphics-device boundary; ownership/array mutations
    // and resource retirement remain in portable code.
    virtual bool release_graphics_object(u32)=0;
};
struct IndependentGraphics {
    std::array<u32,2> animations{};
    u32 surface=0,resource=0,pixels=0,signals=0,active=0;
};
bool cleanup_anm_resource(u32 self,const std::array<u32,2>& animation_heads,ResourceCleanupMemory&); //4828e0
bool cleanup_independent_graphics(IndependentGraphics&,const std::array<u32,2>& animation_heads,ResourceCleanupMemory&); //411470
}
