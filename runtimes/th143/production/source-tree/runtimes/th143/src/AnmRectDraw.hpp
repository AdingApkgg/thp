#pragma once
#include "AnmRenderState.hpp"
#include "AnmTransform.hpp"
#include "AnmPrimitive.hpp"
namespace th143 {
// 47e240 and47e570: untextured XYZRHW/color rectangles, optionally preceded
// by the one-unit larger half-alpha rectangle. Anchors0..2 are supported.
bool draw_anm_rectangle(u32 manager,u32 current_manager,float x,float y,float width,float height,float angle,u32 left,u32 right,u32 anchor_x,u32 anchor_y,bool outlined,u32& depth_test,AnmRenderMemory&,AnmSpriteDevice&,AnmPrimitiveDevice&);
// Rectangle dispatch cases16/20/21/22 in47db40, including431cd0 parent position.
i32 draw_anm_rect_sprite(u32 manager,u32 current_manager,AnmView,const AnmViewport&,u32& depth_test,AnmRenderMemory&,AnmSpriteDevice&,AnmPrimitiveDevice&,AnmTransformHost&);
}
