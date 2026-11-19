#include "SceneCleanup.hpp"

namespace th143 {
namespace {
bool mark_resource(AnmWorld& world,u32 resource){
    for(u32 node:{world.instances.registry.primary_head,world.instances.registry.secondary_head}){
        u32 budget=0;
        while(node){
            auto i=world.instances.registry.nodes.find(node-0x570);
            if(i==world.instances.registry.nodes.end()||++budget>world.states.size())return false;
            auto vm=i->second;node=vm.get(0x574);
            if(vm.get(0x30)==resource)vm.put(0x1c,vm.get(0x1c)|0x20);
        }
    }return true;
}
bool mark_handle(AnmWorld& world,u32 handle){
    auto vm=world.find(handle);if(!vm.data)return true;
    vm.put(0x1c,vm.get(0x1c)|0x20);if(vm.get(0x588))return true;
    u32 child=vm.get(0x584),budget=0;
    while(child){
        auto i=world.instances.registry.nodes.find(child-0x580);
        if(i==world.instances.registry.nodes.end()||++budget>world.states.size())return false;
        i->second.put(0x1c,i->second.get(0x1c)|0x20);child=i->second.get(0x584);
    }return true;
}
bool release_field(AnmView view,u32 at,SceneCleanupHost& host){
    const u32 token=view.get(at);if(token&&!host.release_storage(token,true))return false;
    view.put(at,0);return true;
}
bool clear_handle(AnmView view,u32 at,AnmWorld& world){
    if(!mark_handle(world,view.get(at)))return false;view.put(at,0);return true;
}
}
bool cleanup_player(PlayerState& player,AnmWorld& world,SceneCleanupGlobals& g,SceneCleanupHost& host){
    if(!host.remove_callback(player.get(8))||!host.remove_callback(player.get(12)))return false;
    g.player=0;if(!mark_resource(world,player.get(0x10)))return false;
    if(g.game_flags&1)g.saved_shots=player.get(0x688);
    else if(!release_field({player.data.data()},0x688,host))return false;
    return release_field({player.data.data()},0x5c8,host);
}
bool cleanup_pause_menu(PauseMenu& menu,SceneCleanupGlobals& g,SceneCleanupHost& host){
    auto m=menu.view();if(!host.remove_callback(m.get(8))||!host.remove_callback(m.get(12)))return false;
    for(u32 i=0;i<25;++i){const u32 child=m.get(0x204+i*4);
        if(child&&(!host.destroy_scene_choice(child)||!host.release_storage(child,false)))return false;
    }
    if(!release_field(m,0xfa0,host))return false;g.menu=0;
    return release_field(m,0xf84,host)&&release_field(m,0x9b8,host);
}
bool cleanup_hud_message(AnmView hud,AnmWorld& world,SceneCleanupGlobals& g,SceneCleanupHost& host){
    const bool retained=(g.game_flags&0x11)!=0;
    if(retained){if(!mark_resource(world,hud.get(0x14c)))return false;}
    else if(!host.unload_message_resource())return false;
    hud.put(0x14c,0);
    const u32 message=hud.get(0x198);
    if(message){if(!host.destroy_message(message)||!host.release_storage(message,false))return false;hud.put(0x198,0);}
    if(retained)g.saved_message=hud.get(0x19c);
    else {if(!release_field(hud,0x19c,host))return false;g.saved_message=0;}
    if(!host.deactivate_callback(hud.get(8))||!host.deactivate_callback(hud.get(0x13c)))return false;
    for(u32 at:{0xcc,0xd0,0xdc})if(!clear_handle(hud,at,world))return false;
    for(u32 at=0xe0;at<=0x104;at+=4)hud.put(at,0);
    for(u32 i=0;i<10;++i)if(!clear_handle(hud,0xa4+i*4,world))return false;
    for(u32 at:{0x15c,0x1f8,0x24c,0x2a0})hud.put(at,0);
    hud.put(0x180,hud.get(0x180)|0xe0);return true;
}
bool cleanup_hud(AnmView hud,AnmWorld& world,SceneCleanupGlobals& g,SceneCleanupHost& host){
    if(!cleanup_hud_message(hud,world,g,host))return false;
    for(u32 at:{8,0x13c,12,0x138})if(!host.remove_callback(hud.get(at)))return false;
    hud.put(8,0);hud.put(0x13c,0);
    for(u32 at:{0x108,0x114})if(!clear_handle(hud,at,world))return false;
    for(u32 i=0;i<10;++i)if(!clear_handle(hud,0xa4+i*4,world))return false;
    for(u32 at:{0x50,0x54})if(!clear_handle(hud,at,world))return false;
    if(!mark_resource(world,hud.get(0x2ac)))return false;g.hud=0;return true;
}
}
