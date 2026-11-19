#include "StageProjection.hpp"
#include "StageRcpTable.hpp"
#include <cmath>
namespace th143 {
namespace {
using Matrix=std::array<float,16>;
Matrix multiply(const Matrix& a,const Matrix& b){Matrix out;
    for(u32 i=0;i<4;++i)for(u32 j=0;j<4;++j){const float p=a[i*4]*b[j],q=a[i*4+1]*b[4+j],r=a[i*4+2]*b[8+j],s=a[i*4+3]*b[12+j];float v=p+q;if(i==0||i==3)v+=r+s;else{v+=r;v+=s;}out[i*4+j]=v;}return out;
}
float reciprocal(float value){const u32 raw=word(value),sign=raw&0x80000000,b=raw&0x7fffffff;const u32 e=b>>23;
    if(!e)return real(sign|0x7f800000);if(e==255)return b==0x7f800000?real(sign):real(raw|0x400000);
    const i32 power=i32(e)-127;u32 estimate=stage_rcp_estimates[(b&0x7fffff)>>12]-(u32(power)<<23);
    if(!(estimate&0x7f800000)||(estimate&0x80000000))estimate=0;return real(sign|estimate);
}
}
void project_stage_corners(const StageCamera& camera,const StageVector& translation,const StageCorners& input,StageCorners& output){
    AnmView c{const_cast<u8*>(camera.data.data())};Matrix view,projection,world{},viewport{};
    for(u32 i=0;i<16;++i){view[i]=c.floating(0x60+i*4);projection[i]=c.floating(0xa0+i*4);}
    for(u32 i=0;i<4;++i)world[i*5]=1;for(u32 i=0;i<3;++i)world[12+i]=translation[i];
    viewport[0]=float(double(c.get(0xe8))*.5);viewport[5]=float(double(float(c.get(0xec)))*-.5);viewport[10]=float(double(c.floating(0xf4))-c.floating(0xf0));
    viewport[12]=float(double(c.get(0xe0))+double(c.get(0xe8))*.5);viewport[13]=float(double(c.get(0xe4))+double(float(c.get(0xec)))*.5);viewport[14]=c.floating(0xf0);viewport[15]=1;
    const Matrix combined=multiply(multiply(multiply(world,view),projection),viewport);
    for(u32 i=0;i<16;++i){std::array<float,4> transformed;for(u32 j=0;j<4;++j){float v=input[i][0]*combined[j];v+=input[i][1]*combined[4+j];v+=input[i][2]*combined[8+j];v+=combined[12+j];transformed[j]=v;}
        const float estimate=reciprocal(transformed[3]);float refine=estimate*transformed[3];refine*=estimate;const float twice=estimate+estimate;refine=twice-refine;
        for(u32 j=0;j<3;++j)output[i][j]=transformed[j]*refine;
    }
}
StageVisibility stage_object_visibility(AnmView object,const StageVector& instance,StageCamera& camera,float max_distance,i32 origin_x,i32 origin_y){
    StageVisibility result;auto c=camera.view();StageVector delta;
    for(u32 i=0;i<3;++i){const float center=object.floating(4+i*4)+instance[i],eye=c.floating(i*4)+c.floating(0x3c+i*4);delta[i]=center-eye;}
    float d=delta[1]*delta[1]+delta[0]*delta[0];d+=delta[2]*delta[2];if(d>max_distance){result.distance_rejected=result.culled=true;return result;}
    StageVector center,half,low,high;for(u32 i=0;i<3;++i){center[i]=object.floating(4+i*4);half[i]=object.floating(0x10+i*4)*.5f;low[i]=center[i]-half[i];high[i]=center[i]+half[i];}
    result.corners={StageVector{high[0],high[1],high[2]},StageVector{high[0],high[1],low[2]},StageVector{high[0],low[1],high[2]},StageVector{high[0],low[1],low[2]},StageVector{low[0],high[1],high[2]},StageVector{low[0],high[1],low[2]},StageVector{low[0],low[1],high[2]},StageVector{low[0],low[1],low[2]},StageVector{center[0],low[1],low[2]},StageVector{center[0],high[1],low[2]},StageVector{center[0],low[1],high[2]},StageVector{center[0],high[1],high[2]},StageVector{center[0],low[1],center[2]},StageVector{center[0],high[1],center[2]},StageVector{center[0],low[1],center[2]-half[2]*.5f},StageVector{center[0],high[1],center[2]+half[2]*.5f}};
    project_stage_corners(camera,instance,result.corners,result.screen);result.projected=true;
    const float left=float(origin_x),top=float(origin_y),right=left+384.f,bottom=top+448.f;
    result.bounds={right+8.f,left-8.f,bottom+8.f,top-8.f};
    for(const auto& p:result.screen)if(p[2]>=0.f&&p[2]<=1.f){if(result.bounds[0]>p[0])result.bounds[0]=p[0];if(p[0]>result.bounds[1])result.bounds[1]=p[0];if(result.bounds[2]>p[1])result.bounds[2]=p[1];if(p[1]>result.bounds[3])result.bounds[3]=p[1];}
    result.culled=result.bounds[1]<left||right<result.bounds[0]||result.bounds[3]<top||bottom<result.bounds[2];return result;
}
}
