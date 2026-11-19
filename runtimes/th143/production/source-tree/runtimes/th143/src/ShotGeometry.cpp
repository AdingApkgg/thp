#include "ShotGeometry.hpp"
#include <cmath>
namespace th143 {
bool shot_rectangle_circle(float x,float y,float width,float height,float angle,float cx,float cy,float radius){
    const float dx=cx-x,dy=cy-y,s=float(std::sin(double(-angle))),c=float(std::cos(double(-angle)));
    const float local_x=c*dx-s*dy,local_y=c*dy+s*dx,half_width=width*.5f,half_height=height*.5f;
    const float ax=std::fabs(local_x),ay=std::fabs(local_y);
    if(half_width+radius>=ax&&half_height>=ay)return true;
    if(half_width>=ax&&half_height+radius>=ay)return true;
    const float radius_squared=radius*radius,x1=local_x-half_width,y1=local_y-half_height,x2=half_width+local_x,y2=half_height+local_y;
    if(radius_squared>x1*x1+y1*y1)return true;
    if(radius_squared>x2*x2+y1*y1)return true;
    if(radius_squared>x1*x1+y2*y2)return true;
    return radius_squared>x2*x2+y2*y2;
}
}
