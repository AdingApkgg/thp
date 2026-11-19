#pragma once
#include "AnmState.hpp"
#include <array>
namespace th143 {
struct HudMessageTextCallbackHost {
 virtual ~HudMessageTextCallbackHost()=default;
 virtual AnmView message_callback_visual(u32)=0;
 virtual AnmView message_callback_child(AnmView,i32)=0;
 virtual bool message_callback_transform(AnmView,std::array<float,3>&)=0;
};
// Actual4305d0, called by430740 before each text sprite draw.
bool position_hud_message_text(AnmView message,AnmView text,float viewport_scale,HudMessageTextCallbackHost&);
}
