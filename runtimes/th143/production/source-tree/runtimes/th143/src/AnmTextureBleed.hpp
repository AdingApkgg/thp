#pragma once
#include "AnmState.hpp"
namespace th143 {
//4811d0: fill RGB of zero-alpha texels from the four nonzero-alpha neighbors.
// The physical row pitch and untouched padding are retained.
bool bleed_anm_texture_alpha(u32 format,u32 width,u32 height,u32 pitch,u8* pixels,u32 bytes);
}
