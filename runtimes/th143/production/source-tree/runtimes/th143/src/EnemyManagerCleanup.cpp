#include "EnemyManagerCleanup.hpp"
namespace th143 {
bool cleanup_enemy_manager(AnmView owner,u32 self,u32& global,EnemyManagerCleanupHost& host){
    if(!owner.data||!host.reset_enemy_manager(self))return false;
    for(u32 at:{8u,12u})if(owner.get(at)&&!host.remove_enemy_manager_callback(owner.get(at)))return false;
    const u32 loader=owner.get(0xcc);
    for(u32 at=12;at<0x8c;at+=4){u32 allocation;if(!host.read_enemy_memory(loader+at,&allocation,4))return false;if(allocation&&!host.release_enemy_storage(allocation,true))return false;}
    if(loader){
        u32 table;if(!host.read_enemy_memory(loader+0x8c,&table,4))return false;
        const u32 vtable=0x4c5658;if(!host.write_enemy_memory(loader,&vtable,4))return false;
        if(table){const u32 zero=0;if(!host.release_enemy_storage(table,true)||!host.write_enemy_memory(loader+0x8c,&zero,4))return false;}
        if(!host.release_enemy_storage(loader,false))return false;
    }
    owner.put(0xcc,0);
    for(u32 slot=10;slot<16;++slot)if(!host.unload_enemy_animation(slot))return false;
    global=0;return true;
}
}
