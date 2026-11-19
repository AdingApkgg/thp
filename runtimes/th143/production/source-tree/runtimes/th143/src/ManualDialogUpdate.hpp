#pragma once
#include "AnmState.hpp"
#include <initializer_list>
namespace th143 {
struct ManualDialogUpdateHost:AnmTimerHost {
 virtual bool manual_update_read(u32,void*,u32)=0;
 //432000 returns its output handle here; stack scratch/padding is omitted.
 virtual bool manual_update_call(u32 entry,u32 owner,std::initializer_list<u32>,u32& result)=0;
};
bool update_manual_dialog(AnmView,u32 self,ManualDialogUpdateHost&,i32& result);
}
