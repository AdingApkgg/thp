#include "LaserPathSegment.hpp"
#include <cmath>
namespace th143 {
namespace {
float wrap(float a){u32 count=0;while(a>real(0x40490fdb)){a-=real(0x40c90fdb);if(count++>32)break;}while(real(0xc0490fdb)>a){a+=real(0x40c90fdb);if(count++>32)break;}return a;}
bool vector(float angle,float speed,std::array<float,3>& v){if(!std::isfinite(angle)||!std::isfinite(speed)||std::fabs(angle)>1000000.f)return false;v={float(std::cos(double(angle))*double(speed)),float(std::sin(double(angle))*double(speed)),0.f};return true;}
void length_angle(const std::array<float,3>& v,LaserPathPoint& out){const float xx=v[0]*v[0],yy=v[1]*v[1];out.speed=float(std::sqrt(double(xx+yy)));out.angle=float(std::atan2(double(v[1]),double(v[0])));}
}
bool laser_path_point(AnmView node,float time,LaserPathPoint& out){
 const float t=time-node.floating(8);switch(node.get(0x10)){
 case 0:for(u32 i=0;i<3;++i){const float a=node.floating(0x14+i*4)*t;const float b=a*node.floating(0x30);out.position[i]=node.floating(0x20+i*4)+b;}out.speed=node.floating(0x30);out.angle=node.floating(0x2c);return true;
 case 1:if(node.floating(0x38)<-990.f){const float product=node.floating(0x30)*2.f;const float sum=node.floating(0x34)*t+product,factor=t+1.f;for(u32 i=0;i<3;++i){float x=node.floating(0x14+i*4)*sum;x*=factor;x*=.5f;out.position[i]=node.floating(0x20+i*4)+x;}out.speed=node.floating(0x34)*t+node.floating(0x30);out.angle=node.floating(0x2c);return true;}else{std::array<float,3> a,b;if(!vector(node.floating(0x2c),node.floating(0x30),a)||!vector(node.floating(0x38),node.floating(0x34),b))return false;for(u32 i=0;i<3;++i){a[i]=b[i]+a[i];out.position[i]=node.floating(0x20+i*4)+a[i]*t;}length_angle(a,out);return true;}
 case 2:{if(!std::isfinite(t)||t<-4096.f||t>4096.f)return false;const i32 count=i32(t);float angle=node.floating(0x2c),speed=node.floating(0x30);std::array<float,3> p{node.floating(0x20),node.floating(0x24),node.floating(0x28)},v;for(i32 i=0;i<count;++i){if(!vector(angle,speed,v))return false;angle=wrap(angle+node.floating(0x38));p[0]+=v[0];speed+=node.floating(0x34);p[1]+=v[1];p[2]+=v[2];}if(!vector(angle,speed,v))return false;const float fraction=t-float(std::floor(double(t)));for(u32 i=0;i<3;++i)out.position[i]=p[i]+v[i]*fraction;out.speed=speed;out.angle=angle;return true;}
 default:return true;
 }
}
bool laser_path_previous(AnmView node,const LaserPathPoint& previous,float time,LaserPathPoint& out){
 switch(node.get(0x10)){
 case 0:for(u32 i=0;i<3;++i)out.position[i]=previous.position[i]-node.floating(0x14+i*4)*node.floating(0x30);out.speed=node.floating(0x30);out.angle=node.floating(0x2c);return true;
 case 1:if(node.floating(0x38)<-990.f){const float speed=previous.speed-node.floating(0x34);for(u32 i=0;i<3;++i)out.position[i]=previous.position[i]-node.floating(0x14+i*4)*speed;out.speed=node.floating(0x30)-node.floating(0x34);out.angle=previous.angle;return true;}else{std::array<float,3> a,b;if(!vector(previous.angle,-previous.speed,a)||!vector(node.floating(0x38),-node.floating(0x34),b))return false;for(u32 i=0;i<3;++i){a[i]=b[i]+a[i];out.position[i]=previous.position[i]+a[i];}length_angle(a,out);return true;}
 case 2:{std::array<float,3> v;if(!vector(previous.angle,previous.speed,v)||!std::isfinite(time))return false;const float floor=float(std::floor(double(time))),fraction=time-floor;for(u32 i=0;i<3;++i)out.position[i]=previous.position[i]-v[i]*fraction;out.speed=previous.speed-node.floating(0x34);out.angle=wrap(previous.angle-node.floating(0x38));if(!vector(out.angle,out.speed,v))return false;const float remainder=(1.f-time)+floor;for(u32 i=0;i<3;++i)out.position[i]-=v[i]*remainder;return true;}
 default:return true;
 }
}
}
