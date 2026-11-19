#pragma once
#include "AnmState.hpp"
namespace th143 {
struct HudMessagePortraitControlHost {
 virtual ~HudMessagePortraitControlHost()=default;
 virtual bool portrait_control_read(u32,u32&)=0;
 virtual bool portrait_control_signal(u32,i32,bool immediate)=0;
 virtual AnmView portrait_control_visual(u32)=0;
 virtual bool portrait_control_discard_indicator(AnmView)=0;
};
bool execute_hud_message_portrait_control(AnmView,u8,HudMessagePortraitControlHost&);
}
