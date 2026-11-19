#pragma once
#include "AnmState.hpp"
namespace th143 {
struct ManualDialogFactoryHost {
 virtual ~ManualDialogFactoryHost()=default;
 virtual bool manual_allocate(u32,u32&,AnmView&)=0;
 virtual bool manual_update_callback(u32 entry,u32&,AnmView&)=0;
 virtual bool manual_register(u32,i32 priority,bool drawing)=0;
 virtual bool manual_load_worker(u32 entry,u32 owner)=0;
};
bool create_manual_dialog(u32& global_owner,u32& result,ManualDialogFactoryHost&);
}
