#pragma once
#include "AnmState.hpp"
namespace th143 {
struct MessageDialogLoadHost {
 virtual ~MessageDialogLoadHost()=default;
 virtual bool dialog_request_resource(u32 slot,u32 filename,u32& resource)=0;
 virtual bool dialog_resource_error(u32 format,u32 message)=0;
};
bool load_message_dialog_resource(AnmView owner,AnmView update,AnmView draw,AnmView application,MessageDialogLoadHost&);
}
