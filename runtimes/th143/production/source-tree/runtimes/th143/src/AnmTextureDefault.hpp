#pragma once
#include "AnmTexturePixels.hpp"
namespace th143 {
// D3DX_DEFAULT for the BGRA8888 screenshot path: wrapping triangle weights
// and ordered dither. Device rectangles and ownership are separate.
bool filter_anm_texture_default(u32 width,u32 height,const u8* source,u32 bytes,u32 target_width,u32 target_height,AnmTexturePixels& output);
}
