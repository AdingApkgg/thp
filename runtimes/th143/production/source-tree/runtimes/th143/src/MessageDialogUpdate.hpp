#pragma once
#include "AnmState.hpp"
#include <initializer_list>
namespace th143 {
struct MessageDialogUpdateHost:AnmTimerHost {
 virtual bool dialog_update_read(u32,void*,u32)=0;
 virtual bool dialog_update_write(u32,const void*,u32)=0;
 // Declared lower calls. Arguments exclude ABI padding and scratch addresses.
 // 24 denotes IDirect3DBaseTexture9::PreLoad; 4682c0 takes the position words.
 virtual bool dialog_update_call(u32 entry,u32 owner,std::initializer_list<u32>,std::uint64_t& result)=0;
};
bool update_message_dialog(AnmView,u32 self,MessageDialogUpdateHost&,i32& result);
}
