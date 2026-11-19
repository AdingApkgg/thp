#include "ManualDialogCleanup.hpp"
#include <initializer_list>
namespace th143 {
bool cleanup_manual_dialog(AnmView s,u32& global,u32& resource,ManualDialogCleanupHost& h){
 for(u32 at:{8u,12u})if(s.get(at)&&!h.manual_remove_callback(s.get(at)))return false;
 if(resource){if(!h.manual_destroy_resource(resource)||!h.manual_free_storage(resource))return false;resource=0;}global=0;return true;
}
bool destroy_manual_dialog(u32 token,AnmView s,u32& global,u32& resource,ManualDialogCleanupHost& h){return cleanup_manual_dialog(s,global,resource,h)&&h.manual_free_storage(token);}
}
