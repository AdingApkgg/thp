#pragma once
#include "AnmQuadSubmit.hpp"
#include "ScalarProjection.hpp"
namespace th143 {
// 47b5f0 scalar-projected billboard. Native anchor values0..2 are supported;
// bitfield value3 remains explicitly unsupported (-2).
i32 build_anm_billboard(AnmView vm,AnmView camera,AnmQuad&);
// 47ba90 (plain) /47bac0 (CPU fog): projected quad, optional distance fading,
// then the original47a0b0 colored/UV triangle submission path.
i32 draw_anm_billboard(u32 manager,u32 current,AnmView vm,AnmView camera,AnmQuad&,bool fog,u32 physical_width,u32 physical_height,AnmRenderMemory&,AnmSpriteDevice&);
}
