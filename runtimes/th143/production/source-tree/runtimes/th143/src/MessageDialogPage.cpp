#include "MessageDialogPage.hpp"
namespace th143 {
bool load_message_dialog_page(AnmView app,MessageDialogPageHost& h){
 const u32 initial=h.dialog_page_current();u32 buffer;
 if(!h.dialog_page_file(initial+0x140,initial+0x1c0,buffer))return false;
 auto s=h.dialog_page_owner(h.dialog_page_current());if(!s.data)return false;
 s.put(0x138,buffer);s.put(0x13c,3);app.put(0x99c,0);app.put(0x998,1);return true;
}
bool create_message_dialog_page(AnmView s,const std::array<u32,3>& p,MessageDialogPageHost& h){u32 handle;if(!h.dialog_page_visual(s.get(0x134),9,p,handle))return false;s.put(0x124,handle);return true;}
}
