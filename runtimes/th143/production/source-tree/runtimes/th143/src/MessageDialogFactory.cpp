#include "MessageDialogFactory.hpp"
#include <cstring>
namespace th143 {
bool create_message_dialog(u32& global,u32& result,MessageDialogFactoryHost& host){
 u32 token;AnmView s;if(!host.dialog_allocate(0x1c4,token,s)||!token||!s.data)return false;std::memset(s.data,0,0x1c4);global=token;s.put(0,2);
 u32 callback;AnmView cb;if(!host.dialog_update_callback(0x468a20,callback,cb)||!callback||!cb.data)return false;cb.put(4,cb.get(4)&~2u);cb.put(0x24,token);if(!host.dialog_register(callback,11,false))return false;s.put(8,callback);
 if(!host.dialog_allocate(0x28,callback,cb)||!callback||!cb.data)return false;
 cb.put(0,0);cb.put(4,(cb.get(4)&~3u)|1);cb.put(8,0x468a30);cb.put(0xc,0);cb.put(0x10,0);cb.put(0x14,callback);cb.put(0x18,0);cb.put(0x1c,0);cb.put(0x20,0);cb.put(0x24,token);
 if(!host.dialog_register(callback,69,true))return false;s.put(0xc,callback);
 if(!host.dialog_load_worker(0x468360,token))return false;
 const u32 flags=s.get(0x24);if(!(flags&1)){s.put(0x18,0);s.put(0x14,0xfff0bdc1);s.put(0x1c,0);s.put(0x20,0x4e40b0);s.put(0x24,flags|1);}
 s.put(0x18,0);s.put(0x1c,0);s.put(0x14,0xffffffff);s.put(0x10,0);s.put(0x12c,word(64.f));result=token;return true;
}
}
