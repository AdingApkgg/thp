#include "ScalarProjection.hpp"
#include "StageRcpTable.hpp"
namespace th143 {
namespace {
float reciprocal(float value){const u32 raw=word(value),sign=raw&0x80000000,b=raw&0x7fffffff,e=b>>23;if(!e)return real(sign|0x7f800000);if(e==255)return b==0x7f800000?real(sign):real(raw|0x400000);const i32 power=i32(e)-127;u32 estimate=stage_rcp_estimates[(b&0x7fffff)>>12]-(u32(power)<<23);if(!(estimate&0x7f800000)||(estimate&0x80000000))estimate=0;return real(sign|estimate);}
}
StageVector project_stage_point(AnmView camera,const Matrix4& world,const StageVector& point){Matrix4 view,projection;for(u32 i=0;i<16;++i){view[i]=camera.floating(0x60+i*4);projection[i]=camera.floating(0xa0+i*4);}const auto transform=matrix_multiply(matrix_multiply(world,view),projection);
    std::array<float,4> clip;for(u32 i=0;i<4;++i){const float first=point[1]*transform[4+i]+point[0]*transform[i],second=point[2]*transform[8+i]+transform[12+i];clip[i]=first+second;}
    const float estimate=reciprocal(clip[3]);float refine=estimate*clip[3];refine*=estimate;const float twice=estimate+estimate;refine=twice-refine;StageVector out;for(u32 i=0;i<3;++i)out[i]=clip[i]*refine;
    out[0]=float(((double(out[0])+1.0)*.5)*double(camera.get(0xe8))+double(camera.get(0xe0)));
    out[1]=float(((1.0-double(out[1]))*.5)*double(camera.get(0xec))+double(camera.get(0xe4)));
    out[2]=float((double(camera.floating(0xf4))-camera.floating(0xf0))*double(out[2])+camera.floating(0xf0));return out;
}
}
