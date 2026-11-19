#pragma once
#include "AnmRenderState.hpp"
namespace th143 {
//46ff60: complete ordered D3D9 state initialization and optional pool caches.
bool initialize_graphics(u32 manager,AnmRenderMemory&,AnmSpriteDevice&);
}
