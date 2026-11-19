#include "GameOwnerStartup.hpp"
namespace th143 {
bool GameOwnerStartup::retire_resource(u32 resource){
    for(u32 head:{animations.instances.registry.primary_head,animations.instances.registry.secondary_head}){
        u32 budget=100000;for(u32 node=head;node;){u32 token,next;if(!budget--||!animations.read(node,&token,4)||!animations.read(node+4,&next,4))return false;auto vm=animations.state(token);if(!vm.data)return false;if(vm.get(0x30)==resource)vm.put(0x1c,vm.get(0x1c)|0x20);node=next;}
    }return true;
}
bool GameOwnerStartup::bullets(){if(!(owners.created&8)||!retire_resource(owners.bullets.get(0x9bf6cc)))return false;owners.bullets.reset_storage();return true;}
bool GameOwnerStartup::player(i32 lives,u32 fragments){return (owners.created&1)&&reset_player(owners.player,GameOwnerRuntime::player_self,lives,fragments,animations,host);}
bool GameOwnerStartup::items(){if(!(owners.created&16))return false;owners.items.reset_storage();return true;}
bool GameOwnerStartup::lasers(u32 budget){
    if(!(owners.created&32))return false;AnmView owner{owners.lasers.data()};u32 current=owner.get(0x18);
    auto read=[&](u32 p,u32& v){return owners.read(p,&v,4)||animations.read(p,&v,4);};
    auto write=[&](u32 p,u32 v){return owners.write(p,&v,4)||animations.write(p,&v,4);};
    while(current){u32 next;if(!budget--||!read(current+8,next)||!host.startup_laser_destructor(current))return false;u32 previous,following;if(!read(current+4,previous)||!read(current+8,following)||!write(previous+8,following)||(following&&!write(following+4,previous))||!services.release_game_storage(current))return false;current=next;}
    return true;
}
bool GameOwnerStartup::statistics(GameManagerSceneGlobals& g){return (owners.created&4)&&owners.input.begin_scene(owners.player,g);}
bool GameOwnerStartup::equipment_allocate(u32 n,u32& token,AnmView& out){if(!services.allocate_game_storage(n,token)||!token)return false;owners.storage.push_back({token,std::vector<u8>(std::max(1u,n),services.game_allocation_fill())});out={owners.storage.back().bytes.data()};return true;}
bool GameOwnerStartup::equipment(const PlayerEquipmentGlobals& g){return (owners.created&2)&&activate_player_equipment(owners.equipment,owners.player,g,*this);}
}
