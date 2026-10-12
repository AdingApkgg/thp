#include "ScreenFade.hpp"
#include "AnmRenderer.hpp"
#include "PortTitle.hpp"
#include <algorithm>
namespace th11 {
i32 ScreenFade::update(bool stopped,bool frozen) noexcept {
    if(stopped)return 7;
    if(type==3||(kPortTitle==14&&type==0)){
#if PORT_TITLE == 14
        // 46c419..46c43c performs each multiply/divide/subtract in binary32.
        if(duration)alpha=std::max(0,truncate_int(255.f-float(timer.fractional*255.f)/float(duration)));
#else
        if(duration)alpha=std::max(0,truncate_int(255.-double(timer.fractional)*255./duration));
#endif
        if(timer.current>=duration)return 7;
        timer.tick();return 1;
    }
#if PORT_TITLE == 14
    // 46c98d..46c9a5: a double intermediate can change the integer alpha.
    if(duration)alpha=std::max(0,timer.current<duration?truncate_int(float(timer.fractional*255.f)/float(duration)):255);
#else
    if(duration)alpha=std::max(0,timer.current<duration?truncate_int(double(timer.fractional)*255./duration):255);
#endif
    if(timer.current>=wrapping_add(duration,2))return 7;
    if(!frozen)timer.tick();return 1;
}
void ScreenFade::draw(AnmRenderer& renderer) const {
    // TH14 Stage type2/3 uses 46ca40: full virtual-window vertices, retaining
    // the active viewport. The compositor clips it to the current target.
    if(kPortTitle==14&&(type==2||type==3))renderer.solid_rectangle(0,0,640,480,(u32(alpha)<<24)|color);
    else if(type==5||(kPortTitle==14&&type==0)){renderer.set_viewport({0,0,640,480,0,1});renderer.solid_rectangle(0,0,640,480,(u32(alpha)<<24)|color);}
    else renderer.solid_rectangle(32,16,416,464,(u32(alpha)<<24)|color);
}
void ScreenFades::draw(AnmRenderer& renderer,u32 priority) const {for(const auto& effect:effects)if(effect.priority==priority)effect.draw(renderer);}
}
