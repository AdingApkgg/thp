#include "HudOwner.hpp"
namespace th143 {
namespace {
bool retire_slot(AnmView owner,u32 at,AnmWorld& world){
    if(!world.mark_retirement(owner.get(at)))return false;
    owner.put(at,0);return true;
}
bool retire_resource(AnmWorld& world,u32 resource){
    for(u32 node:{world.instances.registry.primary_head,world.instances.registry.secondary_head}){
        u32 budget=100000;
        while(node){
            u32 token,next;if(!budget--||!world.read(node,&token,4)||!world.read(node+4,&next,4))return false;
            auto vm=world.state(token);if(!vm.data)return false;
            if(vm.get(0x30)==resource)vm.put(0x1c,vm.get(0x1c)|0x20);
            node=next;
        }
    }return true;
}
}
void construct_hud_owner(AnmView owner){std::memset(owner.data,0,0x2b8);owner.put(0,2);}
bool initialize_hud_owner(AnmView owner,u32 self,HudOwnerGlobals& g,Scheduler& scheduler,HudOwnerHost& host,i32& result){
    u32 resource;if(!host.hud_front_resource(resource))return false;owner.put(0x2ac,resource);
    if(!resource){if(!host.hud_load_error())return false;result=-1;return true;}
    if(!load_hud_scene(owner,g.scene,host,result))return false;
    if(result){result=-1;return true;}
    for(auto row:{std::array<u32,4>{0x42ecd0,33,0,8},{0x42ece0,12,0,0x13c},{0x42ecf0,49,1,12},{0x42ed00,46,1,0x138}}){
        u32 token;u8 fill;if(!host.hud_callback_storage(token,fill)||!token||!scheduler.create(token,row[0],fill))return false;
        auto callback=scheduler.at(token);callback.put(4,callback.get(4)&~2u);callback.put(0x24,self);
        u32 ignored;if(!scheduler.add(token,i32(row[1]),row[2]!=0,host,ignored))return false;
        owner.put(row[3],token);
    }result=0;return true;
}
bool cleanup_hud_message(AnmView message,AnmWorld& world){
    for(u32 at=0x40;at<=0x68;at+=4)if(!retire_slot(message,at,world))return false;
    return true;
}
bool reset_hud_scene(AnmView owner,HudOwnerGlobals& g,Scheduler& scheduler,AnmWorld& world,HudOwnerHost& host){
    if(!(g.game_flags&0x11)){
        if(g.scene_resource){if(!host.hud_release_scene_resource(g.scene_resource))return false;g.scene_resource=0;}
    }else if(!retire_resource(world,owner.get(0x14c)))return false;
    owner.put(0x14c,0);
    const u32 message_token=owner.get(0x198);
    if(message_token){
        AnmView message{nullptr};if(!host.hud_message_view(message_token,message)||!message.data||!cleanup_hud_message(message,world)||!host.hud_release_storage(message_token,false))return false;
        owner.put(0x198,0);
    }
    if(!(g.game_flags&0x11)){
        if(owner.get(0x19c)&&!host.hud_release_storage(owner.get(0x19c),true))return false;
        owner.put(0x19c,0);g.scene.pending_file=0;
    }else g.scene.pending_file=owner.get(0x19c);
    for(u32 at:{8,0x13c})if(owner.get(at)){
        auto callback=scheduler.at(owner.get(at));if(!callback.data)return false;callback.put(4,callback.get(4)&~2u);
    }
    for(u32 at:{0xcc,0xd0,0xdc})if(!retire_slot(owner,at,world))return false;
    for(u32 at=0xe0;at<=0x104;at+=4)owner.put(at,0);
    for(u32 at=0xa4;at<=0xc8;at+=4)if(!retire_slot(owner,at,world))return false;
    for(u32 at:{0x15c,0x1f8,0x24c,0x2a0})owner.put(at,0);
    owner.put(0x180,owner.get(0x180)|0xe0);return true;
}
bool cleanup_hud_owner(AnmView owner,HudOwnerGlobals& g,Scheduler& scheduler,AnmWorld& world,HudOwnerHost& host){
    if(!reset_hud_scene(owner,g,scheduler,world,host))return false;
    for(u32 at:{8,0x13c,12,0x138})if(owner.get(at)&&!scheduler.remove(owner.get(at),host))return false;
    owner.put(8,0);owner.put(0x13c,0);
    for(u32 at:{0x108,0x114})if(!retire_slot(owner,at,world))return false;
    for(u32 at=0xa4;at<=0xc8;at+=4)if(!retire_slot(owner,at,world))return false;
    for(u32 at:{0x50,0x54})if(!retire_slot(owner,at,world))return false;
    if(!retire_resource(world,owner.get(0x2ac)))return false;
    g.owner=0;return true;
}
bool destroy_hud_owner(u32 token,HudOwnerGlobals& g,Scheduler& scheduler,AnmWorld& world,HudOwnerHost& host){
    AnmView owner{nullptr};return token&&host.hud_owner_view(token,owner)&&owner.data&&cleanup_hud_owner(owner,g,scheduler,world,host)&&host.hud_release_storage(token,false);
}
bool create_hud_owner(HudOwnerGlobals& g,u32& result,Scheduler& scheduler,AnmWorld& world,HudOwnerHost& host){
    u32 token;AnmView owner{nullptr};if(!host.hud_owner_storage(token,owner)||!token||!owner.data)return false;
    construct_hud_owner(owner);g.owner=token;i32 status;
    if(!initialize_hud_owner(owner,token,g,scheduler,host,status))return false;
    if(status){if(!destroy_hud_owner(token,g,scheduler,world,host))return false;result=0;return true;}
    result=token;return true;
}
bool destroy_current_hud_owner(HudOwnerGlobals& g,Scheduler& scheduler,AnmWorld& world,HudOwnerHost& host){
    return !g.owner||destroy_hud_owner(g.owner,g,scheduler,world,host);
}
}
