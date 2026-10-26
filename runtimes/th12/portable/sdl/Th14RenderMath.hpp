#pragma once
#include "Renderer.hpp"
#include <algorithm>
#include <cmath>
#include <cstring>
namespace touhou::sdl {
#if defined(PORT_TITLE) && PORT_TITLE == 14
// Fixed-function matrix composition rounds every product and partial sum to
// binary32 before the next term. Volatile stores retain that order at -O3.
inline std::array<float,16> th14_multiply(const std::array<float,16>& a,const std::array<float,16>& b){
 std::array<float,16> result{};
 for(int col=0;col<4;++col)for(int row=0;row<4;++row){
  volatile float product=a[row]*b[col*4];volatile float sum=product;
  for(int k=1;k<4;++k){product=a[k*4+row]*b[col*4+k];sum=sum+product;}
  result[col*4+row]=sum;
 }
 return result;
}
inline std::array<float,16> th14_clip(const std::array<float,16>& world,const std::array<float,16>& view,const std::array<float,16>& projection){
 return th14_multiply(projection,th14_multiply(view,world));
}
#endif

#if defined(PORT_TITLE) && PORT_TITLE == 14
inline bool th14_primitive_projectable(const float* vertices,u32 stride,u32 first,u32 count,const std::array<float,16>& clip,const Viewport& viewport){
 // Enclose binary32 dot products under reassociation/FMA and flush-to-zero.
 // Eight full float epsilons exceed the seven-operation gamma bound. Keep
 // subnormal inputs, potential overflow and uncertain W/depth boundaries unchanged. Side clipping is eligible only as a complete primitive.
 constexpr double epsilon=0x1p-23,minimum=0x1p-126,maximum=0x1.fffffep127;
 if(!viewport.width||!viewport.height)return false;
 for(float c:clip)if(!std::isfinite(c)||(c!=0&&std::abs(double(c))<minimum))return false;
 for(u32 i=first;i<first+count;++i){float p[3];std::memcpy(p,reinterpret_cast<const u8*>(vertices)+i*stride,12);
  for(float c:p)if(!std::isfinite(c)||(c!=0&&std::abs(double(c))<minimum))return false;
  double q[4]{},error[4]{};
  for(u32 row=0;row<4;++row){double magnitude=0;for(u32 col=0;col<4;++col){const double product=double(clip[col*4+row])*(col==3?1.:double(p[col]));q[row]+=product;magnitude+=std::abs(product);}
   if(!std::isfinite(magnitude)||magnitude>maximum*.25)return false;
   error[row]=8.*epsilon*magnitude+8.*minimum;
  }
  if((std::abs(q[0])+error[0])*std::max(1.,double(float(viewport.width))*.5)>maximum*.25||(std::abs(q[1])+error[1])*std::max(1.,double(float(viewport.height))*.5)>maximum*.25)return false;
  const double lowW=q[3]-error[3];
  if(!(lowW>0&&q[2]-error[2]>0&&q[2]+error[2]<lowW))return false;
  if((std::abs(q[0])+error[0])*std::max(1.,double(float(viewport.width))*.5)/lowW>maximum/1024.||(std::abs(q[1])+error[1])*std::max(1.,double(float(viewport.height))*.5)/lowW>maximum/1024.)return false;
 }
 return true;
}
#endif
}
