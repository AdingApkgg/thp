#pragma once
#include "AnmState.hpp"
namespace th143 {
struct ManualDialogCleanupHost {
 virtual ~ManualDialogCleanupHost()=default;
 virtual bool manual_remove_callback(u32)=0;
 virtual bool manual_destroy_resource(u32)=0;
 virtual bool manual_free_storage(u32)=0;
};
bool cleanup_manual_dialog(AnmView,u32& global_owner,u32& resource_slot,ManualDialogCleanupHost&);
bool destroy_manual_dialog(u32 token,AnmView,u32& global_owner,u32& resource_slot,ManualDialogCleanupHost&);
}
