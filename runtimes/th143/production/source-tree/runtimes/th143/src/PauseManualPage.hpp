#pragma once
#include "AnmState.hpp"
#include <initializer_list>
namespace th143 {
struct PauseManualPageHost {
 virtual ~PauseManualPageHost()=default;
 virtual bool pause_manual_read(u32,void*,u32)=0;
 virtual bool pause_manual_write(u32,const void*,u32)=0;
 virtual bool pause_manual_call(u32 entry,u32 owner,std::initializer_list<u32>)=0;
};
// Complete4486c0 substate12. Caller supplies the outer pause timers.
bool advance_pause_manual_page(AnmView menu,u32 self,PauseManualPageHost&);
}
