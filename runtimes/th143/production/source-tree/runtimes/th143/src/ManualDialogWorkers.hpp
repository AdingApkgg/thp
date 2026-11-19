#pragma once
#include "AnmState.hpp"
namespace th143 {
struct ManualDialogWorkersHost {
 virtual ~ManualDialogWorkersHost()=default;
 virtual bool manual_region(u32 token,u32 bytes,AnmView&)=0;
 virtual bool manual_request_resource(u32 slot,u32 name,u32& resource)=0;
 virtual bool manual_resource_error(u32 context,u32 message)=0;
 virtual bool manual_read_page(u32 filename,u32 size_out,u32 external,u32& buffer)=0;
};
// Both workers reload the global owner after the external request returns.
bool load_manual_dialog_resource(u32& owner,AnmView application,ManualDialogWorkersHost&);
bool read_manual_dialog_page(u32& owner,AnmView application,ManualDialogWorkersHost&);
}
