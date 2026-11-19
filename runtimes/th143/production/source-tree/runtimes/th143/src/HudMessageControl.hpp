#pragma once
#include "AnmState.hpp"
namespace th143 {
struct HudMessageControlHost {virtual ~HudMessageControlHost()=default;virtual bool message_signal_immediate(u32 handle,i32 signal)=0;};
// Selected actual42f3d0 instruction bodies; caller owns time and PC progression.
bool execute_hud_message_control(AnmView,u8 opcode,const u8* payload,u32 bytes,HudMessageControlHost&);
}
