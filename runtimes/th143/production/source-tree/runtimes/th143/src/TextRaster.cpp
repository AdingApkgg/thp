#include "TextRaster.hpp"
#include <algorithm>

namespace th143 {
namespace {
void put(std::array<u8,108>& b,u32 at,u32 v){std::memcpy(b.data()+at,&v,4);}
}
bool TextRaster::initialize(u32 value,bool alternative,const std::array<TextFont,10>& definitions){
    if(value!=21&&value!=26)return false;format=value;alternative_font=alternative;fonts=definitions;stride=value==21?4096:2048;
    header.fill(0);put(header,0,108);put(header,4,1024);put(header,8,u32(-129));put(header,12,1|((value==21?32u:16u)<<16));
    put(header,16,3);put(header,20,stride*128);
    const std::array<u32,4> masks=value==21?std::array<u32,4>{0xff0000,0xff00,0xff,0xff000000}:std::array<u32,4>{0xf00,0xf0,0xf,0xf000};
    for(u32 i=0;i<4;++i)put(header,40+i*4,masks[i]);bitmap.assign(stride*129,0);return true;
}
bool TextRaster::draw(const std::array<i32,4>& rectangle,i32 x,i32 height,u32 foreground,u32 outline,const u8* bytes,u32 length,i32 kind,i32 character_step,bool shadow,TextRasterHost& host){
    if(bitmap.size()!=stride*129||height>58||length>1024||(!bytes&&length))return false;
    const u32 rows=u32(std::max(height,17)*2+12);std::fill_n(bitmap.begin(),stride*128,u8(0));
    TextPixels pixels{bitmap.data(),u32(bitmap.size()),1024,128,stride,format,scratch_guard};if(!pixels.invert_alpha(rows))return false;
    std::vector<TextDraw> commands;
    auto add=[&](u32 color,i32 px,i32 py,const u8* data,u32 n){commands.push_back({color,px,py,{data,data+n}});};
    if(!character_step){
        x+=2;
        if(shadow){for(const std::array<i32,2>& offset:std::array<std::array<i32,2>,8>{{{1,1},{-1,1},{1,3},{-1,3},{2,2},{-2,2},{0,0},{0,4}}})add(outline,x+offset[0],offset[1],bytes,length);}
        add(foreground,x,2,bytes,length);
    }else{
        // Native uses a fixed two-byte buffer,including the terminating zero
        // for an odd byte count. Pitch advances X; this is not vertical text.
        for(u32 at=0;at<length;at+=2){const u8 pair[2]={bytes[at],at+1<length?bytes[at+1]:u8(0)};
            if(shadow)for(const std::array<i32,2>& offset:std::array<std::array<i32,2>,4>{{{2,4},{-2,4},{2,0},{-2,0}}})add(outline,x+offset[0],offset[1],pair,2);
            add(foreground,x,2,pair,2);x+=character_step;
        }
    }
    constexpr u32 font_index[9]={2,4,3,5,6,8,7,9,1}; // Original46c730 dispatch table.
    if(!host.glyphs(header,fonts[kind>=0&&kind<=8?font_index[kind]:0],commands,bitmap))return false;
    if(bitmap.size()!=stride*129)return false;pixels.data=bitmap.data();pixels.capacity=u32(bitmap.size());
    if(!pixels.invert_alpha(rows)||!pixels.blur_alpha(rows)||!pixels.bleed_color(rows))return false;
    TextUpload request{rectangle,{0,0,std::min(rectangle[2]-rectangle[0],1024),rectangle[3]-rectangle[1]},format,stride};
    if(alternative_font&&kind!=6&&kind!=2){request.source[1]=6;request.source[3]+=6;}
    return host.upload(request,bitmap);
}
}
