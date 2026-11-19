#include "EnemyEffectSpawn.hpp"
namespace th143 {
bool spawn_enemy_effect(AnmResourceWorld& world,u32 token,i32 script,const std::array<float,3>& position,u32& handle){
    auto* resource=world.resource(token);if(!resource||script<0||u32(script)>=resource->templates.size())return false;
    ++world.instances.resource_uses[token];u32 self;AnmView vm;if(!world.acquire_state(self,vm))return false;
    anm_copy_template(vm,self,{resource->templates[u32(script)].data()},world.global_rate_token());
    vm.put(0x1c,vm.get(0x1c)|0x200u);for(u32 i=0;i<3;++i)vm.put(0x59c+i*4,word(position[i]));vm.put(0x50,0);
    return anm_step(vm,static_cast<AnmWorld&>(world))!=-2&&world.instances.registry.insert(vm,self,false,true,handle)&&world.synchronize_resources();
}
}
