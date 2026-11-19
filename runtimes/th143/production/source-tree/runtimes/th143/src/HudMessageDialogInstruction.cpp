#include "HudMessageDialogInstruction.hpp"
namespace th143 {
bool execute_hud_message_dialog_instruction(AnmView message,HudMessageDialogInstructionHost& host){
 if(!host.message_dialog_create())return false;
 auto dialog=host.message_dialog_current();if(!dialog.data)return false;
 dialog.put(0x12c,word(192.f));
 u32 mode;if(!host.message_dialog_read(message.get(0x158)+4,&mode,4))return false;
 dialog.put(0x130,mode);return true;
}
}
