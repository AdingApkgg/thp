#include "MessageDialogLoad.hpp"
namespace th143 {
bool load_message_dialog_resource(AnmView s,AnmView update,AnmView draw,AnmView app,MessageDialogLoadHost& h){
 u32 resource;if(!h.dialog_request_resource(19,0x4c5884,resource))return false;s.put(0x134,resource);
 if(!resource)return h.dialog_resource_error(0x4e20a8,0x4c52bc);
 app.put(0x99c,0);app.put(0x998,1);update.put(4,update.get(4)|2);draw.put(4,draw.get(4)|2);return true;
}
}
