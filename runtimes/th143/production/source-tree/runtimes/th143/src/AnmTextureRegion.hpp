#pragma once
#include "AnmTextureFilter.hpp"
#include <array>
namespace th143 {
// D3DX surface upload into a subrectangle, preserving pixels outside it.
// Transport failure and the original upload HRESULT remain distinct.
bool upload_anm_texture_region(AnmTexturePixels& target,const std::array<i32,4>& destination,u32 source_format,u32 source_width,u32 source_height,const u8* source,u32 source_bytes,const std::array<i32,4>& source_rect,u32 filter,i32& hresult);
}
