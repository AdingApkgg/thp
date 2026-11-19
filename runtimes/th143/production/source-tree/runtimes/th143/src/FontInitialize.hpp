#pragma once
#include "TextRaster.hpp"
#include "Rng.hpp"
namespace th143 {
struct FontInitializeState {
    u32 alternative=0;
    Rng animation;
    std::array<u8,256> noise{};
    std::array<u32,10> handles{};
    std::array<TextFont,10> fonts;
};
using FontFamilyNames=std::array<std::vector<u8>,3>; // MS Gothic, Meiryo, MS Mincho
struct FontInitializeHost {
    virtual ~FontInitializeHost()=default;
    virtual bool font_screen_dc(u32&)=0;
    virtual bool enumerate_font_families(u32,const std::array<u8,60>&,std::vector<std::array<u8,124>>&)=0;
    virtual bool release_font_screen_dc(u32)=0;
    virtual bool initialize_font_bitmap(u32 format,u32& result)=0;
    virtual bool create_initialized_font(const TextFont&,u32& handle)=0;
};
bool observe_font_family(FontInitializeState&,const std::array<u8,124>&,const std::vector<u8>& wanted); //46beb0
bool initialize_fonts(FontInitializeState&,const FontFamilyNames&,FontInitializeHost&); //46bf00
}
