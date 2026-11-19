#pragma once
#include "AnmState.hpp"
#include <vector>
namespace th143 {
struct AnmTexturePixels {u32 format=0,width=0,height=0;std::vector<u8> data;};
u32 anm_texture_pixel_bytes(u32 d3d_format);
// D3DX_FILTER_NONE semantics: crop at the origin and clear uncovered pixels.
// The physical target format/dimensions are explicit device-capability inputs.
bool convert_anm_texture_pixels(u32 source_format,u32 source_width,u32 source_height,const u8*,u32 source_bytes,u32 target_format,u32 target_width,u32 target_height,AnmTexturePixels&);
// Decode raw THTX data; no decoded native pixels are accepted by this API.
bool decode_anm_texture_pixels(const u8* thtx,u32 bytes,u32 target_format,u32 target_width,u32 target_height,AnmTexturePixels&);
}
