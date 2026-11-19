#include "CheatCleanup.hpp"
namespace th143 {
bool cleanup_cheat_owner(AnmView owner,u32& global_owner,Scheduler& scheduler,SchedulerHost& host,AnmWorld& graphics){
    for(u32 at:{8,12})if(owner.get(at)&&!scheduler.remove(owner.get(at),host))return false;
    const u32 resource=owner.get(0x10);
    for(u32 node:{graphics.instances.registry.primary_head,graphics.instances.registry.secondary_head}){
        u32 budget=100000;
        while(node){
            u32 vm,next;if(!budget--||!graphics.read(node,&vm,4)||!graphics.read(node+4,&next,4))return false;
            auto state=graphics.state(vm);if(!state.data)return false;
            if(state.get(0x30)==resource)state.put(0x1c,state.get(0x1c)|0x20);
            node=next;
        }
    }
    global_owner=0;return true;
}
}
