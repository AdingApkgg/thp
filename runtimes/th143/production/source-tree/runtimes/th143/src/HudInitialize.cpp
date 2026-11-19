#include "HudInitialize.hpp"

namespace th143 {
namespace {
bool create(AnmView hud,u32 resource,i32 script,i32 raw_slot,AnmWorld& world,u32& handle){
    auto* r=world.resource(resource);
    if(!r||script<0||u32(script)>=r->templates.size())return false;
    ++world.instances.resource_uses[resource];
    u32 token;AnmView vm;if(!world.acquire_state(token,vm))return false;
    // The two ASCII owners publish the VM before40ab20 and time-zero code.
    if(raw_slot>=0)hud.put(u32(raw_slot),token);
    anm_copy_template(vm,token,{r->templates[script].data()},world.global_rate_token());
    vm.put(0x1c,vm.get(0x1c)|0x200);
    for(u32 at:{0x59c,0x5a0,0x5a4,0x50})vm.put(at,0);
    if(anm_step(vm,world)==-2)return false;
    return world.instances.registry.insert(vm,token,false,false,handle);
}
}
bool initialize_hud(AnmView hud,HudInitializeGlobals& g,AnmWorld& world,HudInitializeHost& host){
    for(u32 at:{8,12,0x138,0x13c})if(u32 callback=hud.get(at)){
        u32 flags;if(!host.hud_callback_read(callback,flags)||!host.hud_callback_write(callback,flags|2))return false;
    }
    u32 handle;
    if(!hud.get(0x120)){
        if(!create(hud,hud.get(0x2ac),0,-1,world,handle))return false;hud.put(0x120,handle);
    }
    if(!hud.get(0x98))for(u32 i=0;i<2;++i){
        u32 resource;if(!host.hud_ascii_resource(resource)||!create(hud,resource,i32(i)+2,0x98+i*4,world,handle))return false;
        hud.put(0x50+i*4,handle);auto vm=world.state(hud.get(0x98+i*4));if(!vm.data)return false;
        vm.put(0x18,vm.get(0x18)&~2u);vm.put(0x1c,vm.get(0x1c)&~0x60000u);
    }
    if(hud.get(0x14c)&&((g.game_flags&0xc00)!=0xc00))
        if(!create(hud,hud.get(0x14c),i32(g.selection),-1,world,handle))return false;
    if(g.game_flags&0x80)if(!create(hud,hud.get(0x2ac),84,-1,world,handle))return false;
    if(!hud.get(0xa0)){
        if(!create(hud,hud.get(0x2ac),101,-1,world,handle))return false;hud.put(0xa0,handle);
    }
    for(u32 at:{0x15c,0x1f8,0x24c,0x2a0})hud.put(at,0);
    hud.put(0x2a8,0xffffffff);return true;
}
}
