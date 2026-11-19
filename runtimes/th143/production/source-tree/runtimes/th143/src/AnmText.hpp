#pragma once
#include "AnmState.hpp"
#include "TextRaster.hpp"

namespace th143 {
struct AnmTextHost:TextRasterHost {
    virtual bool read_text_memory(u32 token,void*,u32)=0;
    virtual bool text_texture(u32 token)=0;
};
// 482e40's literal-format path used by original hint.txt. Unknown printf
// conversions are rejected until the formatted-text service is implemented.
bool anm_text_literal(AnmView,TextRaster&,u32 foreground,u32 outline,i32 font_kind,i32 pitch,const u8* encoded,u32 n,AnmTextHost&);
}
