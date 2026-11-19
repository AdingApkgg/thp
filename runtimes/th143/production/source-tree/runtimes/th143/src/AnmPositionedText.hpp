#pragma once
#include "AnmText.hpp"
namespace th143 {
//482c20 literal-format path: explicit horizontal origin and character pitch.
bool anm_positioned_text_literal(AnmView,TextRaster&,u32 foreground,u32 outline,i32 font_kind,i32 x,i32 pitch,const u8* encoded,u32 bytes,AnmTextHost&);
}
