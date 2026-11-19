#include "CheatFactory.hpp"
namespace th143 {
bool destroy_cheat_owner(u32 token,u32& global_owner,Scheduler& scheduler,AnmWorld& graphics,CheatFactoryHost& host){
    AnmView owner{nullptr};return token&&host.cheat_owner_view(token,owner)&&owner.data&&
        cleanup_cheat_owner(owner,global_owner,scheduler,host,graphics)&&host.cheat_owner_release(token);
}
bool create_cheat_owner(u32& global_owner,u32& result,Scheduler& scheduler,AnmWorld& graphics,CheatFactoryHost& host){
    u32 token;AnmView owner{nullptr};if(!host.cheat_owner_storage(token,owner)||!token||!owner.data)return false;
    construct_cheat_owner(owner);global_owner=token;i32 status;
    if(!initialize_cheat_owner(owner,token,scheduler,host,status))return false;
    if(status){if(!destroy_cheat_owner(token,global_owner,scheduler,graphics,host))return false;result=0;return true;}
    result=token;return true;
}
bool destroy_current_cheat_owner(u32& global_owner,Scheduler& scheduler,AnmWorld& graphics,CheatFactoryHost& host){
    return !global_owner||destroy_cheat_owner(global_owner,global_owner,scheduler,graphics,host);
}
}
