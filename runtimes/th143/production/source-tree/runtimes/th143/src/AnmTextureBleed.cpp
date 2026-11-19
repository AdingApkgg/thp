#include "AnmTextureBleed.hpp"
#include <array>
namespace th143 {
bool bleed_anm_texture_alpha(u32 format,u32 width,u32 height,u32 pitch,u8* pixels,u32 bytes){
    const bool wide=format==0||format==21;if(!wide&&format!=25&&format!=26&&format!=29)return true;if(!width||!height)return true;
    const u32 bpp=wide?4:2;if(!pixels||std::uint64_t(width)*bpp>pitch||pitch%bpp||std::uint64_t(height)*pitch>bytes)return false;
    const u32 alpha=wide?0xff000000u:format==25?0x8000:format==26?0xf000:0xff00;
    const std::array<u32,3> shift=wide?std::array<u32,3>{0,8,16}:format==25?std::array<u32,3>{0,5,10}:format==26?std::array<u32,3>{0,4,8}:std::array<u32,3>{0,2,5};
    const std::array<u32,3> mask=wide?std::array<u32,3>{255,255,255}:format==25?std::array<u32,3>{31,31,31}:format==26?std::array<u32,3>{15,15,15}:std::array<u32,3>{3,7,7};
    auto read=[&](u32 at){u32 value=0;std::memcpy(&value,pixels+at,bpp);return value;};
    for(u32 y=0;y<height;++y)for(u32 x=0;x<width;++x){const u32 at=y*pitch+x*bpp,value=read(at);if(value&alpha)continue;std::array<u32,3> sums{};u32 count=0;auto add=[&](u32 p){const u32 n=read(p);if(n&alpha){for(u32 c=0;c<3;++c)sums[c]+=(n>>shift[c])&mask[c];++count;}};
        if(x)add(at-bpp);if(x+1<width)add(at+bpp);if(y)add(at-pitch);if(y+1<height)add(at+pitch);u32 output=value&alpha;for(u32 c=0;c<3;++c)output|=(count?sums[c]/count:0)<<shift[c];std::memcpy(pixels+at,&output,bpp);
    }return true;
}
}
