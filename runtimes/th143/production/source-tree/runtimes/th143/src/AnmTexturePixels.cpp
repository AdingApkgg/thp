#include "AnmTexturePixels.hpp"
namespace th143 {
u32 anm_texture_pixel_bytes(u32 format){switch(format){case 21:case 22:return 4;case 20:return 3;case 23:case 25:case 26:case 29:return 2;case 28:return 1;default:return 0;}}
namespace {
struct Color {u32 b,g,r,a,mb=255,mg=255,mr=255,ma=255;};
u32 channel(u32 value,u32 source_mask,u32 target_mask){return (value*target_mask+source_mask/2)/source_mask;}
Color unpack(const u8* p,u32 format){if(format==21)return {p[0],p[1],p[2],p[3]};if(format==20||format==22)return {p[0],p[1],p[2],255};if(format==28)return {0,0,0,p[0]};const u32 v=u32(p[0])|(u32(p[1])<<8);
    if(format==23)return {v&31,v>>5&63,v>>11&31,1,31,63,31,1};
    if(format==25)return {v&31,v>>5&31,v>>10&31,v>>15,31,31,31,1};
    if(format==26)return {v&15,v>>4&15,v>>8&15,v>>12,15,15,15,15};
    return {v&3,v>>2&7,v>>5&7,v>>8,3,7,7,255};
}
void pack(u8* p,u32 format,const Color& c){auto b=[&](u32 m){return channel(c.b,c.mb,m);};auto g=[&](u32 m){return channel(c.g,c.mg,m);};auto r=[&](u32 m){return channel(c.r,c.mr,m);};auto a=[&](u32 m){return channel(c.a,c.ma,m);};
    if(format==21||format==22){p[0]=u8(b(255));p[1]=u8(g(255));p[2]=u8(r(255));p[3]=format==22?0:u8(a(255));return;}if(format==20){p[0]=u8(b(255));p[1]=u8(g(255));p[2]=u8(r(255));return;}if(format==28){p[0]=u8(a(255));return;}
    const u32 v=format==23?(r(31)<<11)|(g(63)<<5)|b(31):format==25?(a(1)<<15)|(r(31)<<10)|(g(31)<<5)|b(31):format==26?(a(15)<<12)|(r(15)<<8)|(g(15)<<4)|b(15):(a(255)<<8)|(r(7)<<5)|(g(7)<<2)|b(3);p[0]=u8(v);p[1]=u8(v>>8);
}
}
bool convert_anm_texture_pixels(u32 sf,u32 sw,u32 sh,const u8* source,u32 bytes,u32 df,u32 dw,u32 dh,AnmTexturePixels& out){
    const u32 sb=anm_texture_pixel_bytes(sf),db=anm_texture_pixel_bytes(df);if(!source||!sb||!db||!sw||!sh||!dw||!dh||std::uint64_t(sw)*sh*sb>bytes||std::uint64_t(dw)*dh*db>0x10000000)return false;
    out.format=df;out.width=dw;out.height=dh;out.data.assign(dw*dh*db,0);const u32 w=sw<dw?sw:dw,h=sh<dh?sh:dh;
    for(u32 y=0;y<h;++y)for(u32 x=0;x<w;++x){const u8* p=source+(y*sw+x)*sb;u8* target=out.data.data()+(y*dw+x)*db;if(sf==df)std::memcpy(target,p,sb);else pack(target,df,unpack(p,sf));}return true;
}
bool decode_anm_texture_pixels(const u8* raw,u32 size,u32 format,u32 width,u32 height,AnmTexturePixels& out){
    if(!raw||size<16||std::memcmp(raw,"THTX",4))return false;u16 source_format,sw,sh;u32 bytes;std::memcpy(&source_format,raw+6,2);std::memcpy(&sw,raw+8,2);std::memcpy(&sh,raw+10,2);std::memcpy(&bytes,raw+12,4);static constexpr u32 formats[8]={0,21,25,23,20,26,29,28};if(source_format>=8||bytes>size-16)return false;return convert_anm_texture_pixels(formats[source_format],sw,sh,raw+16,bytes,format,width,height,out);
}
}
