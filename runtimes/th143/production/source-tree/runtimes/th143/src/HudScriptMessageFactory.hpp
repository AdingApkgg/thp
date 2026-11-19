#pragma once
#include "AnmState.hpp"
namespace th143 {
struct HudScriptMessageFactoryHost {
 virtual ~HudScriptMessageFactoryHost()=default;
 virtual bool message_factory_read(u32,u32&)=0;
 virtual bool message_factory_destroy(u32)=0;
 virtual bool message_factory_allocate(u32,u32&,AnmView&)=0;
 virtual bool message_factory_construct(u32,AnmView,u32 script)=0;
};
bool create_hud_script_message(AnmView hud,AnmView root,u32 game_flags,i32 id,HudScriptMessageFactoryHost&);
}
