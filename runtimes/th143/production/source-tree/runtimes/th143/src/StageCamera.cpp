#include "StageCamera.hpp"
#include "AnmRsqrtTable.hpp"
#include <cmath>

namespace th143 {
namespace {
using Vec=std::array<float,3>;
bool normalize(const Vec& v,Vec& out){
    float n=v[0]*v[0];n+=v[1]*v[1];n+=v[2]*v[2];
    if(!std::isfinite(n))return false;
    if(n<real(0x28800000)){out={0,0,0};return true;}
    const u32 b=word(n);const i32 power=i32(b>>23)-127;
    const u32 index=((b&0x7fffff)|((u32(power)&1)<<23))>>12;
    const i32 exponent=power<0?(power-1)/2:power/2;
    const float estimate=real((0x3f000000u+(u32(anm_rsqrt_estimates[index])<<11))-(u32(exponent)<<23));
    float r=estimate*n;r*=estimate;const float half=estimate*.5f;r=3.f-r;r*=half;
    for(u32 i=0;i<3;++i)out[i]=v[i]*r;return true;
}
Vec cross_extended(const Vec& a,const Vec& b){
    return {float(double(a[1])*b[2]-double(a[2])*b[1]),
            float(double(a[2])*b[0]-double(a[0])*b[2]),
            float(double(a[0])*b[1]-double(a[1])*b[0])};
}
float dot_extended(const Vec& a,const Vec& b){return float((double(a[0])*b[0]+double(a[1])*b[1])+double(a[2])*b[2]);}
}
bool prepare_stage_camera(StageCamera& camera,StageCameraServices& host){
    auto s=camera.view();if(host.has_animation_manager()&&!host.flush_stage_camera_batch())return false;
    Vec eye,focus,direction,up;
    for(u32 i=0;i<3;++i){eye[i]=s.floating(i*4)+s.floating(0x3c+i*4);direction[i]=s.floating(0x24+i*4);focus[i]=eye[i]+direction[i];up[i]=s.floating(0x18+i*4);}
    Vec z,x;for(u32 i=0;i<3;++i)z[i]=float(double(focus[i])-eye[i]);
    if(!normalize(z,z)||!normalize(cross_extended(up,z),x))return false;const Vec y=cross_extended(z,x);
    for(u32 i=0;i<3;++i){s.put(0x60+i*16,word(x[i]));s.put(0x64+i*16,word(y[i]));s.put(0x68+i*16,word(z[i]));s.put(0x6c+i*16,0);}
    s.put(0x90,word(-dot_extended(x,eye)));s.put(0x94,word(-dot_extended(y,eye)));s.put(0x98,word(-dot_extended(z,eye)));s.put(0x9c,word(1.f));
    const float aspect=float(s.get(0xe8))/float(s.get(0xec));
    const float half=s.floating(0x54)*.5f;
    const float sine=float(std::sin(double(half))),cosine=float(std::cos(double(half)));
    const float height=cosine/sine,depth=float(8000.0/(8000.0-30.0));
    if(!std::isfinite(aspect)||!std::isfinite(height))return false;
    for(u32 i=0;i<16;++i)s.put(0xa0+i*4,0);
    s.put(0xa0,word(height/aspect));s.put(0xb4,word(height));s.put(0xc8,word(depth));s.put(0xcc,word(1.f));s.put(0xd8,word(float(-double(depth)*30.0)));
    if(!host.set_stage_camera_transform(2,camera.data.data()+0x60)||!host.set_stage_camera_transform(3,camera.data.data()+0xa0))return false;
    // This game-side cross product uses SSE float intermediates and the
    // opposite orientation to the right vector of the D3DX view matrix.
    Vec side;side[0]=up[2]*direction[1]-up[1]*direction[2];side[1]=up[0]*direction[2]-up[2]*direction[0];side[2]=up[1]*direction[0]-up[0]*direction[1];
    if(!normalize(side,side))return false;for(u32 i=0;i<3;++i)s.put(0x30+i*4,word(side[i]));
    return !host.has_animation_manager()||host.set_stage_camera_origin(s.get(0xfc),s.get(0x100));
}
}
