#include "LaserCircleInterval.hpp"
#include <cmath>
namespace th143 {
bool laser_circle_interval(const std::array<float,3>& origin,const std::array<float,3>& center,float angle,float radius,float& begin,float& end,bool& intersects){
 if(!std::isfinite(angle)||!std::isfinite(radius)||!(radius>0.f)||!std::isfinite(origin[0])||!std::isfinite(origin[1])||!std::isfinite(center[0])||!std::isfinite(center[1]))return false;
 const float dx=center[0]-origin[0],dy=center[1]-origin[1],sine=float(std::sin(double(-angle))),cosine=float(std::cos(double(-angle)));
 const float y=sine*dx+cosine*dy,x=cosine*dx-sine*dy;intersects=false;
 if(std::fabs(y)>radius||-radius>x)return true;
 if(0.f>x&&x*x+y*y>radius*radius)return true;
 const float ratio=y/radius,square=ratio*ratio,extent=float(std::sqrt(double(1.f-square)))*radius;
 begin=x-extent;end=x+extent;intersects=true;return true;
}
}
