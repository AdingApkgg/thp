#pragma once
#include "HudMessageControl.hpp"
#include "AnmInterpolation.hpp"
namespace th143 {
struct HudMessageInput {u32 fresh=0,held=0,confirm_counter=0,skip_counter=0;};
struct HudMessageFlowHost:HudMessageControlHost,AnmTimerHost {
 virtual bool message_read(u32,void*,u32)=0;
 virtual bool message_play_sound(i32)=0;
 virtual AnmView message_visual(u32)=0;
 virtual bool message_external_instruction(AnmView,u8,const u8*,u32){return false;}
 // Starts after the first indicator lookup. Missing indicators are handled here.
 virtual bool message_indicator(AnmView,AnmView,i32&){return false;}
};
bool step_hud_message_flow(AnmView,const HudMessageInput&,HudMessageFlowHost&,i32& result,u32 instruction_budget=100000);
}
