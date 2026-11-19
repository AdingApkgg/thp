#include "GameEnemyCleanupRuntime.hpp"
namespace th143 {
bool GameEnemyCleanupRuntime::map(u32 p,void* b,u32 n,bool write){
    auto bytes=[&](u32 base,void* data,u32 size){if(p<base||std::uint64_t(p)+n>std::uint64_t(base)+size)return false;auto* at=static_cast<u8*>(data)+p-base;if(write)std::memcpy(at,b,n);else std::memcpy(b,at,n);return true;};
    if(bytes(GameEnemyRuntime::self,owner.data.data(),owner.data.size()))return true;
    if(bytes(scheduler.self,scheduler.data.data(),scheduler.data.size()))return true;
    for(auto& [base,data]:scheduler.records)if(bytes(base,data.data(),data.size()))return true;
    for(auto& h:headers){
        if(bytes(h.actor->token,&h.vtable,4)||bytes(h.actor->token+0x11d0,h.links.data(),16))return true;
        if(n==4&&p>=h.actor->token+0x11f0&&p+4<=h.actor->token+0x53d8){u32 value;if(write){std::memcpy(&value,b,4);h.actor->state.put(p-h.actor->token-0x11f0,value);}else{value=h.actor->state.get(p-h.actor->token-0x11f0);std::memcpy(b,&value,4);}return true;}
    }
    for(auto& node:nodes)if(bytes(node.token,node.data.data(),16))return true;
    return false;
}
bool GameEnemyCleanupRuntime::read_retained(u32 p,void* b,u32 n){return map(p,b,n,false)||owner.read(p,b,n)||animations.read(p,b,n)||services.read_enemy_cleanup_memory(p,b,n);}
bool GameEnemyCleanupRuntime::write_enemy_memory(u32 p,const void* b,u32 n){return map(p,const_cast<void*>(b),n,true)||animations.write(p,b,n)||services.write_enemy_cleanup_memory(p,b,n);}
bool GameEnemyCleanupRuntime::reset(){
    if(!owner.global_owner||scripts.failed)return false;
    for(auto* actor:scripts.live){
        Header header{actor,0x4c563c,{actor->token,0,0,0}};u32 previous=actor->token+0x11d0;std::size_t prior=nodes.size();
        for(auto* thread=actor->owner.threads.next;thread;thread=thread->next){u32 vm,node;if(!thread->value||!services.enemy_thread_identity(*thread->value,vm,node)||!vm||!node)return false;
            const u32 fill=u32(services.enemy_cleanup_allocation_fill())*0x01010101u;nodes.push_back({node,{vm,0,previous,fill}});
            if(previous==actor->token+0x11d0)header.links[1]=node;else nodes[prior-1].data[1]=node;previous=node;prior=nodes.size();
        }
        headers.push_back(header);
    }
    std::array<u32,6> resources{};for(const auto& r:animations.resources)if(r.file>=10&&r.file<16)resources[r.file-10]=r.token;
    if(!reset_enemies(GameEnemyRuntime::self,resources,{animations.instances.registry.primary_head,animations.instances.registry.secondary_head},*this))return false;
    for(auto* actor:scripts.live){actor->owner.cancel_secondary();actor->retired=true;}
    scripts.live.clear();scripts.active=nullptr;
    for(auto& actor:scripts.storage)retired.push_back(std::move(actor));scripts.storage.clear();
    for(u32 i=0;i<scripts.controls.bosses.size();++i)scripts.controls.bosses[i]=owner.view().get(0x5c+i*4);
    return true;
}
}
