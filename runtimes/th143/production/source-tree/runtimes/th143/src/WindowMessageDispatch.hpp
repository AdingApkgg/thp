#pragma once
#include "AnmState.hpp"
#include <initializer_list>
namespace th143 {
struct WindowMessageDispatchHost {
 virtual ~WindowMessageDispatchHost()=default;
 virtual bool window_message_read(u32 address,u32& value)=0;
 virtual bool window_message_write(u32 address,u32 value)=0;
 // Fixed import-slot identities. Implementations retain the platform call order.
 virtual bool window_message_call(u32 import_slot,std::initializer_list<u32>,u32& result)=0;
};
// Complete original registered window procedure46e770..46e9ce.
// ShowCursor follows the original signed-counter loops; the host must terminate them.
bool dispatch_window_message(u32 window,u32 message,u32 wparam,u32 lparam,WindowMessageDispatchHost&,u32& result);
}
