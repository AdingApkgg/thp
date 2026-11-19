#pragma once
#include "AnmState.hpp"
#include <initializer_list>
namespace th143 {
struct TitleOptionControlHost:AnmTimerHost {
 virtual bool title_option_read(u32,void*,u32)=0;
 virtual bool title_option_write(u32,const void*,u32)=0;
 virtual bool title_option_call(u32 entry,u32 owner,std::initializer_list<u32>,u32& result)=0;
};
// Full4601d0, actual cursor/60frame preview trigger, and45f6e0 outerclock.
//460540 view/volume propagation andstate4 key configuration are separate.
bool advance_title_option_control(AnmView title,u32 self,TitleOptionControlHost&,u32& result);
}
