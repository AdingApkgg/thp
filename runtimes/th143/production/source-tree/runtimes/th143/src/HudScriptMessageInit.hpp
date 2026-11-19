#pragma once
#include "AnmState.hpp"
namespace th143 {
struct HudScriptMessageInitHost {
 virtual ~HudScriptMessageInitHost()=default;
 // 483f00 with zero position/rotation, layer-1, space4 and trailing0.
 virtual bool message_create_text(u32 resource,i32 script,u32& handle)=0;
 virtual bool message_signal_text(u32 handle,i32 signal)=0;
 virtual AnmView message_text_vm(u32 handle)=0;
};
bool initialize_hud_script_message(AnmView,u32 script,u32 text_resource,HudScriptMessageInitHost&);
}
