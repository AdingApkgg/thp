#pragma once
#include "AnmState.hpp"
#include <initializer_list>
namespace th143 {
struct TitleManualPageHost:AnmTimerHost {
 virtual bool title_manual_read(u32,void*,u32)=0;
 virtual bool title_manual_write(u32,const void*,u32)=0;
 //483a70 returns the inserted handle; scratch output pointers are omitted.
 virtual bool title_manual_call(u32 entry,u32 owner,std::initializer_list<u32>,u32& result)=0;
};
//45f6e0 state5 -> full466480 and the outer Title timer; music flag clear.
bool advance_title_manual_page(AnmView,u32 self,TitleManualPageHost&,u32& result);
}
