#pragma once
#include "AnmState.hpp"
namespace th143 {
struct HudMessageDialogInstructionHost {
 virtual ~HudMessageDialogInstructionHost()=default;
 virtual bool message_dialog_create()=0;
 virtual AnmView message_dialog_current()=0;
 virtual bool message_dialog_read(u32,void*,u32)=0;
};
// Actual42f3d0 opcode33: factory callbacks may replace both global owner and MSG PC.
bool execute_hud_message_dialog_instruction(AnmView,HudMessageDialogInstructionHost&);
}
