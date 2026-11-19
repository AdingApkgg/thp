#pragma once
#include "AnmText.hpp"
namespace th143 {
//482d10 centers encoded text in the sprite's full-width coordinate space.
bool anm_centered_text_literal(AnmView,TextRaster&,u32 foreground,u32 outline,i32 font_kind,i32 pitch,const u8*,u32 bytes,AnmTextHost&);
}
