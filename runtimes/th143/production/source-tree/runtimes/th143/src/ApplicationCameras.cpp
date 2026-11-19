#include "ApplicationCameras.hpp"
#include "AnmRsqrtTable.hpp"
#include <cmath>
namespace th143 {
namespace {
using Vec=std::array<float,3>;
bool normalize(const Vec& v,Vec& out){float n=v[0]*v[0];n+=v[1]*v[1];n+=v[2]*v[2];if(!std::isfinite(n))return false;if(n<real(0x28800000)){out={0,0,0};return true;}
    const u32 b=word(n);const i32 power=i32(b>>23)-127,index=((b&0x7fffff)|((u32(power)&1)<<23))>>12,exponent=power<0?(power-1)/2:power/2;
    const float estimate=real((0x3f000000u+(u32(anm_rsqrt_estimates[index])<<11))-(u32(exponent)<<23));float r=estimate*n;r*=estimate;const float half=estimate*.5f;r=3.f-r;r*=half;for(u32 i=0;i<3;++i)out[i]=v[i]*r;return true;}
Vec cross(const Vec& a,const Vec& b){return {float(double(a[1])*b[2]-double(a[2])*b[1]),float(double(a[2])*b[0]-double(a[0])*b[2]),float(double(a[0])*b[1]-double(a[1])*b[0])};}
float dot(const Vec& a,const Vec& b){return float((double(a[0])*b[0]+double(a[1])*b[1])+double(a[2])*b[2]);}
bool integer(float v,i32& out){if(!std::isfinite(v)||double(v)>=2147483648.||double(v)<-2147483648.){out=i32(0x80000000u);return true;}out=i32(v);return true;}
}
bool initialize_pixel_camera(AnmView s){if(!s.data)return false;
    const float x=float(s.get(0xe0))+float(s.get(0xe8))*.5f,y=float(s.get(0xe4))+float(s.get(0xec))*.5f;
    const float half=s.floating(0x54)*.5f,tangent=float(std::tan(double(half)));const float distance=float(s.get(0xec)>>1)/tangent;
    const Vec eye{x,y,distance},up{0,-1,0};Vec z{0,0,float(0.-double(distance))},right;if(!normalize(z,z)||!normalize(cross(up,z),right))return false;const Vec vertical=cross(z,right);
    for(u32 i=0;i<3;++i){s.put(0x60+i*16,word(right[i]));s.put(0x64+i*16,word(vertical[i]));s.put(0x68+i*16,word(z[i]));s.put(0x6c+i*16,0);}
    s.put(0x90,word(-dot(right,eye)));s.put(0x94,word(-dot(vertical,eye)));s.put(0x98,word(-dot(z,eye)));s.put(0x9c,word(1.f));
    const float aspect=float(s.get(0xe8))/float(s.get(0xec)),sine=float(std::sin(double(half))),cosine=float(std::cos(double(half))),height=cosine/sine,depth=float(10000./9999.);
    if(!std::isfinite(aspect)||!std::isfinite(height))return false;for(u32 i=0;i<16;++i)s.put(0xa0+i*4,0);s.put(0xa0,word(height/aspect));s.put(0xb4,word(height));s.put(0xc8,word(depth));s.put(0xcc,word(1.f));s.put(0xd8,word(-depth));return true;
}
bool initialize_application_cameras(AnmView app,const ApplicationCameraConfig& config,std::array<i32,2>& origin){if(!app.data)return false;auto base=app.sub(0x488);
    for(u32 i=0;i<3;++i){base.put(i*4,0);base.put(0xc+i*4,0);base.put(0x18+i*4,i==1?word(1.f):0);base.put(0x3c+i*4,0);base.put(0x48+i*4,0);}
    base.put(0x54,0x3f060a92);base.put(0xe0,0);base.put(0xe4,0);base.put(0xe8,config.width);base.put(0xec,(config.flags&0x3c)==8?960:config.height);base.put(0xf0,0);base.put(0xf4,word(1.f));base.put(0xf8,2);base.put(0x58,config.width);base.put(0x5c,config.height);
    if(!initialize_pixel_camera(base))return false;std::memcpy(app.data+0x230,base.data,300);auto play=app.sub(0x230);play.put(0xf8,0);
    const float factors[4]={128,16,384,448};for(u32 i=0;i<4;++i){i32 v;integer(config.scale*factors[i],v);play.put(0xe0+i*4,u32(v));}if(!initialize_pixel_camera(play))return false;
    std::memcpy(app.data+0x35c,play.data,300);auto alternate=app.sub(0x35c);alternate.put(0xf8,1);for(u32 i=0;i<4;++i){i32 v;integer(config.scale*factors[i],v);alternate.put(0xe0+i*4,u32(v));}if(!initialize_pixel_camera(alternate))return false;
    std::memcpy(app.data+0x5b4,play.data,300);auto stage=app.sub(0x5b4);stage.put(0xf8,3);i32 x,y;integer((float(i32(config.width))-408.f)*.5f,x);integer((float(i32(config.height))-472.f)*.5f,y);stage.put(0xe0,u32(x));stage.put(0xe4,u32(y));stage.put(0xe8,408);stage.put(0xec,472);if(!initialize_pixel_camera(stage))return false;
    origin[0]=i32(config.width)/2;integer(config.scale*16.f,origin[1]);return true;
}
}
