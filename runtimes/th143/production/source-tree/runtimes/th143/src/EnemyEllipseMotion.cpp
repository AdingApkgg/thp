#include "EnemyEllipseMotion.hpp"
#include "DirectionVector.hpp"
#include <cmath>
namespace th143 {
namespace {float wrap(float v){u32 count=0;while(v>real(0x40490fdb)){v-=real(0x40c90fdb);if(count++>32)break;}while(real(0xc0490fdb)>v){v+=real(0x40c90fdb);if(count++>32)break;}return v;}float quantize(float v){return float(std::floor(double(v*100.f)))/100.f;}}
bool evaluate_enemy_ellipse(AnmView p){
    float phase=p.floating(0x1c),orientation=p.floating(0x28),delta=phase-orientation;
    if(delta>real(0x40490fdb))delta=phase-(orientation+real(0x40c90fdb));
    else if(orientation-phase>real(0x40490fdb))delta=phase-(orientation-real(0x40c90fdb));
    delta=wrap(delta);delta=wrap(delta);
    const float radius=p.floating(0x20);if(!std::isfinite(delta)||!std::isfinite(radius)||!std::isfinite(orientation))return false;
    DirectionVector v{float(std::cos(double(delta))*double(radius)),float(std::sin(double(delta))*double(radius))};
    const float stretched=p.floating(0x2c)*v.x,sine=float(std::sin(double(orientation))),cosine=float(std::cos(double(orientation)));
    const float y=(v.y*cosine)+(sine*stretched),x=(cosine*stretched)-(v.y*sine);
    p.put(0,word(quantize(p.floating(0x34)+x)));p.put(4,word(quantize(p.floating(0x38)+y)));p.put(8,word(p.floating(0x3c)+0.f));return true;
}
}
