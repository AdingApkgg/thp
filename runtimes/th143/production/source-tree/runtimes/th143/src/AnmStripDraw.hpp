#pragma once
#include "AnmMeshDraw.hpp"
#include "AnmPrimitive.hpp"
namespace th143 {
// 47cf30: reset/rebuild XYZ Euler world matrix, fixed-function texture state,
// then upload the VM-owned 24-byte XYZ/color/UV triangle strip.
i32 draw_anm_strip(u32 manager,u32 current_manager,AnmView,u32 vertices,u32 count,const AnmViewport&,u32& depth_test,AnmRenderMemory&,AnmSpriteDevice&,AnmMeshDevice&,AnmPrimitiveDevice&);
// 40a120 callback: depth-write1,draw32 strip vertices,then depth-write0.
bool draw_anm_effect5(u32 manager,u32 current_manager,AnmView,const AnmViewport&,u32& depth_test,u32& depth_write,AnmRenderMemory&,AnmSpriteDevice&,AnmMeshDevice&,AnmPrimitiveDevice&);
}
