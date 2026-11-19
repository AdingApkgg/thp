#include "AnmManager.hpp"

namespace th143 {
bool AnmManager::retire(AnmRegistry& r,u32 self,AnmVmHost& host,AnmStorageHost& storage){
    auto found=r.nodes.find(self);if(found==r.nodes.end())return false;AnmView s=found->second;
    const u32 node=self+0x570;
    for(u32* tail:{&r.primary_tail,&r.secondary_tail})if(*tail==node)*tail=s.get(0x578);
    for(u32* head:{&r.primary_head,&r.secondary_head})if(*head==node)*head=s.get(0x574);
    r.sync_owner();
    if(s.get(0x5c0)){
        float rate;i32 result;if(!host.timer_rate(host.global_rate_token(),rate)||!host.callback(s.get(0x5c0),s,rate,result))return false;
    }
    auto set_node=[&](u32 pointer,u32 base,u32 at,u32 value){
        auto target=r.nodes.find(pointer-base);if(target==r.nodes.end())return false;
        target->second.put(at,value);return true;
    };
    if(s.get(0x574)&&!set_node(s.get(0x574),0x570,0x578,s.get(0x578)))return false;
    if(s.get(0x578)&&!set_node(s.get(0x578),0x570,0x574,s.get(0x574)))return false;
    s.put(0x574,0);s.put(0x578,0);
    if(!s.get(0x588)){
        u32 child=s.get(0x584),budget=0;
        while(child){
            auto at=r.nodes.find(child-0x580);if(at==r.nodes.end()||++budget>r.nodes.size())return false;
            auto vm=at->second;vm.put(0x594,0);vm.put(0x1c,vm.get(0x1c)|0x20);child=vm.get(0x584);
        }
    }
    if(s.get(0x584)&&!set_node(s.get(0x584),0x580,0x588,s.get(0x588)))return false;
    if(s.get(0x588)&&!set_node(s.get(0x588),0x580,0x584,s.get(0x584)))return false;
    s.put(0x584,0);s.put(0x588,0);
    if(!storage.prepare_instance_release(self,s))return false;
    if(s.get(0x5b4)&&!storage.release_buffer(s.get(0x5b4)))return false;
    s.put(0x5b4,0);
    if(!storage.release_instance(self))return false;
    r.nodes.erase(self);++retired;return true;
}
bool AnmManager::update(AnmRegistry& r,AnmVmHost& host,AnmStorageHost& storage){
    draws.fill(0);std::array<u32,35> tails{};
    u32 node=r.primary_head,budget=0;
    while(node){
        auto at=r.nodes.find(node-0x570);if(at==r.nodes.end()||++budget>100000)return false;
        auto vm=at->second;const u32 self=node-0x570,next=vm.get(0x574);
        failed_self=self;
        i32 result=0;if(!(vm.get(0x1c)&0x20))result=anm_step(vm,host);else result=1;
        if(result==-2)return false;
        if(result){if(!retire(r,self,host,storage))return false;}
        else{
            const u32 layer=vm.get(0x24);if(layer>=draws.size())return false;
            if(tails[layer]){
                auto previous=r.nodes.find(tails[layer]);if(previous==r.nodes.end())return false;previous->second.put(0x590,self);
            }else draws[layer]=self;
            vm.put(0x590,0);tails[layer]=self;
        }
        ++visited;node=next;
    }
    failed_self=0;return true;
}
}
