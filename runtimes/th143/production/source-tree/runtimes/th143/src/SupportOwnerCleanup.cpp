#include "SupportOwnerCleanup.hpp"
namespace th143 {
bool cleanup_player_auxiliary(AnmView view,u32& owner,SupportOwnerCleanupHost& host){
    for(u32 at:{8,12})if(view.get(at)&&!host.remove_support_callback(view.get(at)))return false;
    for(u32 at:{0x10,0x14}){
        if(!view.get(at))continue;
        if(!host.destroy_support_option(view,at))return false;
        const u32 remaining=view.get(at);
        if(remaining){if(!host.release_support_option(remaining))return false;view.put(at,0);}
    }
    owner=0;return true;
}
bool cleanup_scene_extra(AnmView view,AnmWorld& graphics,u32& owner,SupportOwnerCleanupHost& host){
    for(u32 at:{0x14,0x18,0x1c}){if(!graphics.mark_retirement(view.get(at)))return false;view.put(at,0);}
    for(u32 at:{8,12})if(view.get(at)&&!host.remove_support_callback(view.get(at)))return false;
    owner=0;return true;
}
}
