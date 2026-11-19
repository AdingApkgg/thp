#include "AnmTextureDefault.hpp"
#include <array>
#include <cmath>
namespace th143 {
namespace {
struct Weight {u32 index;float value;};
using Axis=std::vector<std::vector<Weight>>;
Axis weights(u32 source,u32 target){Axis result(target);const float ratio=float(double(target)/source),half_inverse=float(.5/double(ratio));
    for(u32 i=0;i<source;++i){u32 last=0;float accumulated=0;auto flush=[&](){if(accumulated>=1e-5f)result[last].push_back({i,accumulated});accumulated=0;};
        for(u32 pass=0;pass<2;++pass){const float center=float(double(float(i))+pass-.5),left=float(double(center)*ratio),right=float(double(left)+ratio);
            for(i32 k=i32(std::floor(double(left)));float(k)<right;++k){const float l=left>float(k)?left:float(k),r=right<float(k+1)?right:float(k+1);const u32 at=u32((k%i32(target)+i32(target))%i32(target));if(at!=last){flush();last=at;}
                const float factor=float((double(l)+r)*half_inverse-center);const double value=pass?1.-double(factor):double(factor);accumulated=float((double(r)-l)*value+accumulated);
            }
        }flush();
    }return result;
}
}
bool filter_anm_texture_default(u32 sw,u32 sh,const u8* source,u32 bytes,u32 dw,u32 dh,AnmTexturePixels& out){
    if(sw==dw&&sh==dh)return convert_anm_texture_pixels(21,sw,sh,source,bytes,21,dw,dh,out);
    if(!source||!sw||!sh||!dw||!dh||sw>65535||sh>65535||dw>65535||dh>65535||std::uint64_t(sw)*sh*4>bytes||std::uint64_t(dw)*dh*4>0x10000000)return false;
    out.format=21;out.width=dw;out.height=dh;out.data.assign(dw*dh*4,0);const auto xs=weights(sw,dw),ys=weights(sh,dh);static constexpr u32 dither[4][4]={{15,7,13,5},{9,1,11,3},{12,4,14,6},{10,2,8,0}};const float inverse=float(1./255);
    for(u32 y=0;y<dh;++y)for(u32 x=0;x<dw;++x){std::array<double,4> color{};for(const auto& wy:ys[y])for(const auto& wx:xs[x]){const auto* pixel=source+(wy.index*sw+wx.index)*4;const float weight=wy.value*wx.value;for(u32 c=0;c<4;++c){const float sample=float(double(pixel[c])*inverse);color[c]=float(double(sample)*weight+color[c]);}}
        // The horizontal phase on odd rows depends on the row width.
        const double bias=(dither[y&3][(x-(y&1)*dw)&3]+.5)/16;for(u32 c=0;c<4;++c){const double value=color[c]*255+bias;out.data[(y*dw+x)*4+c]=value<=0?0:value>=255?255:u8(u32(value));}
    }return true;
}
}
