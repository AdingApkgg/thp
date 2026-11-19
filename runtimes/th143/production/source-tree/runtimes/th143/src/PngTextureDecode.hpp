#pragma once
#include "AnmTexturePixels.hpp"
namespace th143 {
// Decode PNG source bytes to the BGRA8888 surface representation used by D3DX.
// Decode failure returnsfalse; device upload/HRESULT handling is separate.
bool decode_png_texture(const u8* source,u32 bytes,AnmTexturePixels& output);
}
