#pragma once
#include "AnmSpriteDraw.hpp"
#include "AnmPrimitive.hpp"
namespace th143 {
//47db40 mode17 /47e640: untextured triangle fan, with distinct center
// and rim colors. Includes the common entry's callback/visibility/depth work.
i32 draw_anm_fan_sprite(u32 manager,u32 current,AnmView,const AnmViewport&,u32& depth_test,AnmRenderMemory&,AnmSpriteDevice&,AnmPrimitiveDevice&,AnmSpriteDrawHost&);
//47d5f0 /47da40: already-generated XYZRHW/color/UV strips (9/12/13/14)
// and fans (11). The complete VM-owned28-byte vertices are uploaded unchanged.
i32 draw_anm_geometry_sprite(u32 manager,u32 current,AnmView,u32& depth_test,AnmRenderMemory&,AnmSpriteDevice&,AnmPrimitiveDevice&,AnmSpriteDrawHost&);
}
