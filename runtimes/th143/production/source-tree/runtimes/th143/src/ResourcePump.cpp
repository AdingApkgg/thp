#include "ResourcePump.hpp"

namespace th143 {
namespace {
constexpr u32 table=0xbc7b0c;
bool read(ResourcePumpMemory& h,u32 p,u32& v){return h.read_enemy_memory(p,&v,4);}
bool write(ResourcePumpMemory& h,u32 p,u32 v){return h.write_enemy_memory(p,&v,4);}
bool unload(u32 slot,const std::array<u32,2>& heads,ResourcePumpMemory& h){
    u32 resource;if(!read(h,slot,resource))return false;
    return !resource||(cleanup_anm_resource(resource,heads,h)&&h.release_enemy_storage(resource,false)&&write(h,slot,0));
}
}
bool pump_anm_resources(u32 manager,const std::array<u32,2>& heads,ResourcePumpMemory& h,i32& result){
    for(u32 i=0;i<30;++i){const u32 slot=manager+table+i*4;u32 resource,retiring,pending;
        if(!read(h,slot,resource))return false;if(!resource)continue;
        if(!read(h,resource+0x12c,retiring))return false;
        if(retiring){
            if(!unload(slot,heads,h)||!read(h,slot,resource))return false;
            // Original482814 reloads the now cleared slot before this write.
            // Keep the attempted NULL+12c write visible to the memory host;
            // an unmapped address must fail instead of silently fixing it.
            if(!write(h,resource+0x12c,0))return false;
        }else{
            if(!read(h,resource+0x128,pending))return false;
            if(pending){u32 completed;if(!h.complete_resource_chunk(resource,completed))return false;result=completed?0:-1;return true;}
        }
    }result=0;return true;
}
bool anm_resources_ready(u32 manager,ResourcePumpMemory& h,bool& ready){
    for(u32 i=0;i<30;++i){u32 resource,retiring,pending;if(!read(h,manager+table+i*4,resource))return false;if(!resource)continue;
        if(!read(h,resource+0x12c,retiring)||!read(h,resource+0x128,pending))return false;
        if(retiring||pending){ready=false;return true;}
    }ready=true;return true;
}
bool unload_anm_slot(u32 manager,u32 index,const std::array<u32,2>& heads,ResourcePumpMemory& h){
    return index>=30||unload(manager+table+index*4,heads,h);
}
}
