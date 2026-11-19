#pragma once
#include "AnmState.hpp"
#include <array>
namespace th143 {
struct HudMessageWindowHost {
 virtual ~HudMessageWindowHost()=default;
 virtual AnmView message_window_visual(u32)=0;
 virtual AnmView message_window_state(u32)=0;
 virtual bool message_window_read(u32,u32&)=0;
 virtual bool message_window_create(u32,i32,const std::array<float,3>&,u32&)=0;
 virtual AnmView message_window_child(AnmView,i32)=0;
};
bool retire_hud_message_window(AnmView,HudMessageWindowHost&);
bool create_hud_message_window(AnmView,u32 resource,i32 index,float x,float y,float width,HudMessageWindowHost&);
bool resize_hud_message_window(AnmView,i32 index,float width,HudMessageWindowHost&);
}
