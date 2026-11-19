#pragma once
#include "AnmState.hpp"
namespace th143 {
struct MessageDialogCleanupHost {
 virtual ~MessageDialogCleanupHost()=default;
 virtual bool dialog_remove_callback(u32)=0;
 virtual bool dialog_destroy_resource(u32)=0;
 virtual bool dialog_free_storage(u32)=0;
};
bool cleanup_message_dialog(AnmView,u32& global_owner,u32& resource_slot,MessageDialogCleanupHost&);
bool destroy_message_dialog(u32 token,AnmView,u32& global_owner,u32& resource_slot,MessageDialogCleanupHost&);
}
