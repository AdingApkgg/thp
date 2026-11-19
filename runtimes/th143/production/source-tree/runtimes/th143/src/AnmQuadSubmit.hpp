#pragma once
#include "AnmRenderState.hpp"
namespace th143 {
// 47a0b0: origin/pixel alignment, cached positions, UV/color, viewport reject,
// texture/vertex-kind caches, rendering state and six-vertex batch append.
// rounding is the x87 rounding-control field: nearest/down/up/toward-zero.
bool submit_anm_quad(u32 manager,u32 current_manager,AnmView vm,AnmView camera,AnmQuad&,u32 flags,AnmRenderMemory&,AnmSpriteDevice&,u32 rounding=0);
}
