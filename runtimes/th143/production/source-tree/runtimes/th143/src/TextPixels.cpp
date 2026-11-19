#include "TextPixels.hpp"
#include <vector>

namespace th143 {
namespace {
u16 get16(const u8* p){u16 v;std::memcpy(&v,p,2);return v;}
void put16(u8* p,u16 v){std::memcpy(p,&v,2);}
bool length(TextPixels& s,u32 rows,u32 bytes){return rows<=s.height&&std::uint64_t(s.stride)*rows<=s.capacity&&std::uint64_t(s.width)*bytes*rows<=s.capacity;}
}
bool TextPixels::invert_alpha(u32 rows){
    if(format!=21&&format!=25&&format!=26)return false;
    if(!length(*this,rows,format==21?4:2))return false;
    const u32 bytes=stride*rows;
    if(format==21){for(u32 at=3;at<bytes;at+=4)data[at]=u8(~data[at]);}
    else{
        if(bytes&1)return false;
        for(u32 at=0;at<bytes;at+=2){const u16 old=get16(data+at);u16 value;
            if(format==25)value=(old&0x8000)?0:u16(old|0x8000);
            else{const u16 alpha=u16((old^0xf000)&0xf000);value=u16((old&0xfff)|(alpha&&alpha!=0xf000?0xf000:alpha));}
            put16(data+at,value);
        }
    }return true;
}
bool TextPixels::blur_alpha(u32 rows){
    if(format!=26)return true;if(!length(*this,rows,2))return false;
    // Native copies and walks width*rows words, irrespective of stride. It
    // skips each first column, but intentionally includes the last column.
    const u32 n=width*rows;std::vector<u8> copy(std::size_t(n)*2+2);
    std::memcpy(copy.data(),data,std::size_t(n)*2);put16(copy.data()+std::size_t(n)*2,scratch_guard);
    if(rows<=2||!width)return true;
    for(u32 i=0;i<width*(rows-2);++i){
        const u32 at=width+i;
        if(i%width==0)continue;const u16 old=get16(copy.data()+at*2);if(old&0xf000)continue;
        auto alpha=[&](u32 index){return u32(get16(copy.data()+index*2)>>12);};
        const u32 sum=2*(alpha(at-width)+alpha(at+width)+alpha(at-1)+alpha(at+1))+
            alpha(at-width-1)+alpha(at-width+1)+alpha(at+width-1)+alpha(at+width+1);
        put16(data+at*2,u16((get16(data+at*2)&0xfff)|((sum/14)<<12)));
    }return true;
}
bool TextPixels::bleed_color(u32 rows){
    if(format!=21&&format!=26)return true;const u32 pixel=format==21?4:2;
    if(!length(*this,rows,pixel)||stride%pixel)return false;
    // Native advances densely through rows, yet uses stride for vertical
    // neighbors. A bounds check rejects input that would leave owned bytes.
    for(u32 y=0;y<rows;++y)for(u32 x=0;x<width;++x){
        const std::int64_t at=std::int64_t((std::uint64_t(y)*width+x)*pixel);
        if(at+pixel>capacity)return false;
        if(pixel==2?(get16(data+at)&0xf000)!=0:data[at+3]!=0)continue;
        u32 sum[3]{},count=0;
        auto add=[&](std::int64_t offset){
            if(offset<0||std::uint64_t(offset)+pixel>capacity)return false;
            if(pixel==2){const u16 v=get16(data+offset);if(!(v&0xf000))return true;for(u32 c=0;c<3;++c)sum[c]+=(v>>(c*4))&15;}
            else{if(!data[offset+3])return true;for(u32 c=0;c<3;++c)sum[c]+=data[offset+c];}
            ++count;return true;
        };
        if(x&&!add(at-pixel))return false;if(x+1<width&&!add(at+pixel))return false;
        if(y&&!add(at-stride))return false;if(y+1<height&&!add(at+stride))return false;
        if(count>1)for(auto& c:sum)c/=count;
        if(pixel==2){u16 v=u16(get16(data+at)&0xf000);for(u32 c=0;c<3;++c)v|=u16((sum[c]>>1)<<(c*4));put16(data+at,v);}
        else for(u32 c=0;c<3;++c)data[at+c]=u8(sum[c]);
    }return true;
}
}
