#include "MessageDialogCleanup.hpp"
#include <initializer_list>
namespace th143 {
bool cleanup_message_dialog(AnmView s,u32& global,u32& resource,MessageDialogCleanupHost& h){
 for(u32 at:{8u,12u})if(s.get(at)&&!h.dialog_remove_callback(s.get(at)))return false;
 if(resource){if(!h.dialog_destroy_resource(resource)||!h.dialog_free_storage(resource))return false;resource=0;}global=0;return true;
}
bool destroy_message_dialog(u32 token,AnmView s,u32& global,u32& resource,MessageDialogCleanupHost& h){return cleanup_message_dialog(s,global,resource,h)&&h.dialog_free_storage(token);}
}
