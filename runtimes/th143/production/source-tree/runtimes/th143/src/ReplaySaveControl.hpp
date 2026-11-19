#pragma once
#include "AnmState.hpp"
#include <initializer_list>
namespace th143 {
struct ReplaySaveControlHost {
 virtual ~ReplaySaveControlHost()=default;
 virtual bool replay_menu_read(u32,void*,u32)=0;
 virtual bool replay_menu_write(u32,const void*,u32)=0;
 virtual bool replay_menu_call(u32 entry,u32 owner,std::initializer_list<u32>,u32& result)=0;
};
// Full4492a0;0 idle,1 name entry prepared,2 cancelled. The enclosing menu
// callback advances its timers separately. Stored names have13 readable bytes.
bool control_replay_save_list(AnmView menu,u32 self,u32 return_count,ReplaySaveControlHost&,u32& result);
}
