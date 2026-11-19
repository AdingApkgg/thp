#pragma once
#include "AnmTexturePixels.hpp"
namespace th143 {
// D3DX_FILTER_TRIANGLE|MIRROR_U|MIRROR_V (30004), used by481c40 forflag22.
bool filter_anm_texture_pixels(u32 source_format,u32 source_width,u32 source_height,const u8*,u32 bytes,u32 target_format,u32 target_width,u32 target_height,AnmTexturePixels&);
}
