#pragma once
#include "AnmWorld.hpp"
namespace th143 {
struct AsciiDrawHost {
    virtual ~AsciiDrawHost()=default;
    //47aae0 position construction then47a0b0 submission withflags1.
    virtual bool draw_ascii_glyph(AnmView)=0;
};
//40bbb0: font selection,position/alignment,spacing,newlines andshadow/main
// passes. Only the renderer/device submission is supplied by the host.
bool draw_ascii_text(AnmView owner,AnmView entry,AnmWorld&,AsciiDrawHost&);
//40bac0 loop only; flush andcamera restoration belong to the presentation host.
bool draw_ascii_layer(AnmView owner,u32 layer,AnmWorld&,AsciiDrawHost&);
}
