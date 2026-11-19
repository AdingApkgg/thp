#include "AnmPositionedText.hpp"
namespace th143 {
namespace {u32 truncate(float v){return v>=-2147483648.f&&v<2147483648.f?u32(i32(v)):0x80000000;}}
bool anm_positioned_text_literal(AnmView vm,TextRaster& raster,u32 foreground,u32 outline,i32 kind,i32 x,i32 pitch,const u8* bytes,u32 n,AnmTextHost& host){
    constexpr i32 heights[12]={17,17,17,17,21,21,21,21,14,12,4,4};if(kind<0||kind>=12||n>=120||(!bytes&&n))return false;for(u32 i=0;i<n;++i)if(!bytes[i]||bytes[i]=='%')return false;
    std::array<u8,72> descriptor;if(!host.read_text_memory(vm.get(0x2c),descriptor.data(),descriptor.size()))return false;AnmView sprite{descriptor.data()};u32 texture;if(!host.read_text_memory(sprite.get(8),&texture,4))return false;
    const i32 height=heights[kind];if(height>8){std::array<i32,4> rect;for(u32 i=0;i<4;++i)rect[i]=signed_word(truncate(sprite.floating(12+i*4)));const bool shadow=(vm.get(0x1c)&0x800)==0;if(!host.text_texture(texture)||!raster.draw(rect,signed_word(u32(x)*2),height,foreground,shadow?outline:0,bytes,n,kind,signed_word(u32(pitch)*2),shadow,host))return false;}
    vm.put(0x18,vm.get(0x18)|1);return true;
}
}
