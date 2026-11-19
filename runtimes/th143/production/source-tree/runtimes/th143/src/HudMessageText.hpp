#pragma once
#include "AnmState.hpp"
#include <array>
namespace th143 {
struct HudMessageTextHost {
 virtual ~HudMessageTextHost()=default;
 virtual AnmView message_text_resolve(u32& handle)=0;
 virtual bool message_text_draw(AnmView,u32 foreground,u32 outline,i32 kind,i32 x,i32 pitch,const u8*,u32)=0;
 virtual bool message_text_signal(u32,i32,bool immediate)=0;
 virtual bool message_text_position(u32& handle,const std::array<float,3>&)=0;
 virtual bool message_text_window(AnmView,i32,float,float,float)=0;
 virtual bool message_text_width(AnmView,i32,float)=0;
};
bool execute_hud_message_text(AnmView,const u8* encoded,u32 bytes,HudMessageTextHost&);
}
