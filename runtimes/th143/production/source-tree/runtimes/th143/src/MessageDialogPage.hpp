#pragma once
#include "AnmState.hpp"
#include <array>
namespace th143 {
struct MessageDialogPageHost {
 virtual ~MessageDialogPageHost()=default;
 virtual u32 dialog_page_current()const=0;
 virtual AnmView dialog_page_owner(u32)=0;
 virtual bool dialog_page_file(u32 filename,u32 size_output,u32& buffer)=0;
 virtual bool dialog_page_visual(u32 resource,i32 script,const std::array<u32,3>& position,u32& handle)=0;
};
bool load_message_dialog_page(AnmView application,MessageDialogPageHost&);
bool create_message_dialog_page(AnmView,const std::array<u32,3>& position,MessageDialogPageHost&);
}
