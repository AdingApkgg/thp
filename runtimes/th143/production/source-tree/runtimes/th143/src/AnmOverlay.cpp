#include "AnmOverlay.hpp"

namespace th143 {
bool AnmOverlay::create(AnmWorld& world,u32 token,i32 script,const std::array<float,3>* position,float rotation,i32 layer,u32 flags,u32& handle){
    auto* resource=world.resource(token);if(!resource||script<0||u32(script)>=resource->templates.size()||(!position&&(flags&8)))return false;
    u32 self;AnmView vm;if(!world.acquire_state(self,vm))return false;++world.instances.resource_uses[token];
    anm_copy_template(vm,self,{resource->templates[script].data()},world.global_rate_token());vm.put(0x1c,vm.get(0x1c)|0x200);
    if(layer>=0){vm.put(0x24,u32(layer));if(layer<=23)vm.put(0x1c,(vm.get(0x1c)&~0x40000u)|0x20000);}
    if(position){for(u32 i=0;i<3;++i)vm.put(0x59c+i*4,word((*position)[i]));
        if(flags&1){vm.put(0x59c,word((*position)[0]+320.f));vm.put(0x5a0,word((*position)[1]+16.f));}}
    else for(u32 i=0;i<3;++i)vm.put(0x59c+i*4,0);
    vm.put(0x50,word(rotation));if(anm_step(vm,world)==-2){u16 opcode=0;world.read(vm.get(0x28),&opcode,2);world.error=opcode;return false;}
    if(!world.instances.registry.insert(vm,self,(flags&4)!=0,(flags&2)!=0,handle))return false;
    if(flags&4)vm.put(0x1c,vm.get(0x1c)&~0x6000u);return true;
}
bool AnmOverlay::update(AnmWorld& world){
    draws.fill(0);std::array<u32,7> tails{};world.manager.visited=0;
    auto& registry=world.instances.registry;u32 node=registry.secondary_head,budget=0;
    while(node){
        auto it=registry.nodes.find(node-0x570);if(it==registry.nodes.end()||++budget>100000)return false;
        auto vm=it->second;const u32 self=node-0x570,next=vm.get(0x574);world.manager.failed_self=self;
        i32 result=vm.get(0x1c)&0x20?1:anm_step(vm,world);if(result==-2)return false;
        if(result){if(!world.manager.retire(registry,self,world,world))return false;}
        else{
            i32 layer=signed_word(vm.get(0x24));if(layer>=24&&layer<=30)layer+=11;else if(layer<35||layer>41)layer=37;
            vm.put(0x24,u32(layer));const u32 index=u32(layer-35);
            if(tails[index]){auto prior=registry.nodes.find(tails[index]);if(prior==registry.nodes.end())return false;prior->second.put(0x590,self);}
            else draws[index]=self;vm.put(0x590,0);tails[index]=self;
        }
        ++world.manager.visited;node=next;
    }
    world.manager.failed_self=0;if(world.pool){auto p=world.pool->view();p.put(0xd8,world.manager.visited);for(u32 i=0;i<7;++i)p.put(0xfe8228+(35+i)*0x5cc+0x590,draws[i]);}return true;
}
}
