#include "AnmTextureFilter.hpp"
#include <array>
#include <cmath>
namespace th143 {
namespace {
using Color=std::array<double,4>;
struct Weight {u32 index;float value;};
using Axis=std::vector<std::vector<Weight>>;
// Pinned D3DX100dc63b scatters each source tent in two passes, rounding the
// ratio, endpoints, factor and running weight tofloat. Transpose only after
// forming these weights; a direct double-precision gather changes pixels.
Axis weights(u32 source,u32 target){Axis result(target);const float ratio=float(double(target)/source),half_inverse=float(.5/double(ratio));
    for(u32 i=0;i<source;++i){u32 last=0;float accumulated=0;
        auto flush=[&](){if(accumulated>=1e-5f)result[last].push_back({i,accumulated});accumulated=0;};
        for(u32 pass=0;pass<2;++pass){const float center=float(double(float(i))+pass-.5);float left=float(double(center)*ratio),right=float(double(left)+ratio);if(left<0)left=0;if(right>float(target))right=float(target);
            for(i32 k=i32(std::floor(double(left)));float(k)<right;++k){const float l=left>float(k)?left:float(k),r=right<float(k+1)?right:float(k+1);if(u32(k)!=last){flush();last=u32(k);}
                float factor;if(center<0)factor=1;else if(double(center)+1>source)factor=0;else factor=float((double(l)+r)*half_inverse-center);
                const double value=pass?1.-double(factor):double(factor);accumulated=float((double(r)-l)*value+accumulated);
            }
        }flush();
    }return result;
}
// The original converter multiplies by a float reciprocal. Direct division
// rounds differently at a few packed-channel thresholds after filtering.
double norm(u32 v,u32 mask){const float inverse=float(1./mask);return float(double(v)*inverse);}
Color unpack(const u8* p,u32 format){if(format==21)return {norm(p[0],255),norm(p[1],255),norm(p[2],255),norm(p[3],255)};if(format==20||format==22)return {norm(p[0],255),norm(p[1],255),norm(p[2],255),1};if(format==28)return {0,0,0,norm(p[0],255)};const u32 v=u32(p[0])|(u32(p[1])<<8);
    if(format==23)return {norm(v&31,31),norm(v>>5&63,63),norm(v>>11&31,31),1};if(format==25)return {norm(v&31,31),norm(v>>5&31,31),norm(v>>10&31,31),double(v>>15)};if(format==26)return {norm(v&15,15),norm(v>>4&15,15),norm(v>>8&15,15),norm(v>>12,15)};return {norm(v&3,3),norm(v>>2&7,7),norm(v>>5&7,7),norm(v>>8,255)};
}
u32 channel(double value,u32 max){value=value*max+.5;if(value<=0)return 0;if(value>=max)return max;return u32(value);}
void pack(u8* p,u32 format,const Color& c){if(format==21||format==22||format==20){for(u32 i=0;i<3;++i)p[i]=u8(channel(c[i],255));if(format!=20)p[3]=format==22?0:u8(channel(c[3],255));return;}if(format==28){p[0]=u8(channel(c[3],255));return;}
    u32 v;if(format==23)v=(channel(c[2],31)<<11)|(channel(c[1],63)<<5)|channel(c[0],31);else if(format==25)v=(channel(c[3],1)<<15)|(channel(c[2],31)<<10)|(channel(c[1],31)<<5)|channel(c[0],31);else if(format==26)v=(channel(c[3],15)<<12)|(channel(c[2],15)<<8)|(channel(c[1],15)<<4)|channel(c[0],15);else v=(channel(c[3],255)<<8)|(channel(c[2],7)<<5)|(channel(c[1],7)<<2)|channel(c[0],3);p[0]=u8(v);p[1]=u8(v>>8);
}
}
bool filter_anm_texture_pixels(u32 sf,u32 sw,u32 sh,const u8* source,u32 bytes,u32 df,u32 dw,u32 dh,AnmTexturePixels& out){
    if(sw==dw&&sh==dh)return convert_anm_texture_pixels(sf,sw,sh,source,bytes,df,dw,dh,out);
    const u32 sb=anm_texture_pixel_bytes(sf),db=anm_texture_pixel_bytes(df);if(!source||!sb||!db||!sw||!sh||!dw||!dh||sw>65535||sh>65535||dw>65535||dh>65535||std::uint64_t(sw)*sh*sb>bytes||std::uint64_t(dw)*dh*db>0x10000000)return false;
    out.format=df;out.width=dw;out.height=dh;out.data.assign(dw*dh*db,0);const auto xs=weights(sw,dw),ys=weights(sh,dh);
    // 100dfefd stores the product weight tofloat, then each x87 multiply/add
    // result tofloat. Preserve source-row/source-column accumulation order.
    for(u32 y=0;y<dh;++y)for(u32 x=0;x<dw;++x){Color color{};for(const auto& wy:ys[y])for(const auto& wx:xs[x]){const Color sample=unpack(source+(wy.index*sw+wx.index)*sb,sf);const float weight=wy.value*wx.value;for(u32 i=0;i<4;++i)color[i]=float(double(float(sample[i]))*weight+color[i]);}pack(out.data.data()+(y*dw+x)*db,df,color);}return true;
}
}
