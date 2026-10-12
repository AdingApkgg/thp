#include "SceneCamera.hpp"
#include <cmath>
namespace th11 {
void SceneCamera::perspective(){
    const auto add=[](Vec3 a,Vec3 b){return Vec3{float(double(a.x)+b.x),float(double(a.y)+b.y),float(double(a.z)+b.z)};};
#if PORT_TITLE == 13 || PORT_TITLE == 14
    // 43ba20 uses the direction cached by the preceding Stage update.
    const auto eye=add(position,eye_offset);
    view=GraphicsMath::look_at(eye,add(eye,reserved24),up);
#else
    view=GraphicsMath::look_at(add(position,eye_offset),add(position,direction),up);
#endif
    projection=GraphicsMath::perspective(fov,float(double(viewport.width)/viewport.height),30,kPortTitle==14?8000:1800);
    right=GraphicsMath::normalize(GraphicsMath::cross(kPortTitle==13||kPortTitle==14?reserved24:direction,up));
}
void SceneCamera::screen(){
    const float width=float(viewport.width),height=float(viewport.height),x=float(double(width)*.5),y=float(double(height)*.5);
    const float tangent=float(std::tan(double(0.15707963705062866f))),distance=float(double(y)/tangent);
    view=GraphicsMath::look_at({x,y,distance},{x,y,0},{0,-1,0});
    projection=GraphicsMath::perspective(0.3141592741012573f,float(double(width)/height),1,10000);
}
}
