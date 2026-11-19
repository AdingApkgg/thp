#pragma once
#include "AnmState.hpp"
namespace th143 {
struct HudSpecialMessageHost {
 virtual ~HudSpecialMessageHost()=default;
 virtual bool special_message_read(u32,void*,u32)=0;
 virtual bool special_message_write(u32,const void*,u32)=0;
 virtual AnmView special_message_audio()=0;
 virtual bool special_message_game_over(u32 reason)=0;
 virtual bool special_message_statistics_begin(u32 root)=0;
};
// Actual42f160 special IDs -1/-2/-3. Positive IDs use the existing factory.
bool create_hud_special_message(AnmView root,u32 game_flags,i32 id,HudSpecialMessageHost&);
}
