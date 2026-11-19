#pragma once
#include "AnmRenderState.hpp"
#include "AnmPrimitive.hpp"
namespace th143 {
// 47d5f0: caller-owned XYZRHW/color/UV triangle strip. Unlike 47db40,
// this entry does not run a VM callback or change the depth-test global.
i32 draw_anm_external_geometry(u32 manager,u32 current,AnmView,u32 vertices,u32 vertex_count,AnmRenderMemory&,AnmSpriteDevice&,AnmPrimitiveDevice&);
}
