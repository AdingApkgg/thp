#include "LaserCleanup.hpp"

namespace th143 {
bool cleanup_laser_manager(u32 self,u32& current,LaserCleanupMemory& host){
    auto read=[&](u32 p,u32& v){return host.read_enemy_memory(p,&v,4);};
    auto write=[&](u32 p,u32 v){return host.write_enemy_memory(p,&v,4);};
    for(u32 at:{8,12}){u32 callback;if(!read(self+at,callback)||!host.remove_laser_callback(callback))return false;}
    u32 laser;if(!read(self+0x18,laser))return false;u32 budget=100000;
    while(laser){u32 cached,next,previous;if(!budget--||!read(laser+8,cached)||!host.destroy_laser(laser)||!read(laser+4,previous)||!read(laser+8,next)||!write(previous+8,next))return false;
        if(next&&!write(next+4,previous))return false;
        if(!host.release_enemy_storage(laser,false))return false;laser=cached;
    }current=0;return true;
}
}
