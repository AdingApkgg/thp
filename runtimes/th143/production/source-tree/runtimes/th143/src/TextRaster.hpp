#pragma once
#include "TextPixels.hpp"
#include <array>
#include <vector>

namespace th143 {
struct TextFont {std::array<i32,13> arguments{};std::vector<u8> face;};
struct TextDraw {u32 color; i32 x,y;std::vector<u8> bytes;};
struct TextUpload {std::array<i32,4> destination,source;u32 format,stride;};
struct TextRasterHost {
    virtual ~TextRasterHost()=default;
    virtual bool glyphs(const std::array<u8,108>& header,const TextFont&,const std::vector<TextDraw>&,std::vector<u8>& bitmap)=0;
    virtual bool upload(const TextUpload&,const std::vector<u8>& bitmap)=0;
};
// 46ade0 bitmap descriptor and46c3f0 CPU text layout/filters/upload request.
// The OS glyph API and final texture transfer belong to the host.
struct TextRaster {
    u32 format=26,stride=2048;
    bool alternative_font=false;
    std::array<u8,108> header{};
    std::vector<u8> bitmap;
    std::array<TextFont,10> fonts;
    u16 scratch_guard=0;
    bool initialize(u32 format,bool alternative,const std::array<TextFont,10>&);
    bool draw(const std::array<i32,4>& rectangle,i32 x,i32 height,u32 foreground,u32 outline,
              const u8* bytes,u32 length,i32 font_kind,i32 character_step,bool shadow,TextRasterHost&);
};
}
