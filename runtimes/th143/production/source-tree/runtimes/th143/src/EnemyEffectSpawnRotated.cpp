#include "EnemyEffectSpawnRotated.hpp"
namespace th143 {
bool spawn_rotated_enemy_effect(AnmResourceWorld& world,u32 token,i32 script,AnmView actor,Vm& command,VmHost& host,u32& handle){
 auto* resource=world.resource(token);if(!actor.data||!resource||script<0||u32(script)>=resource->templates.size())return false;
 ++world.instances.resource_uses[token];u32 self;AnmView vm;if(!world.acquire_state(self,vm))return false;
 anm_copy_template(vm,self,{resource->templates[u32(script)].data()},world.global_rate_token());
 vm.put(0x1c,vm.get(0x1c)|0x200u);
 for(u32 i=0;i<3;++i)vm.put(0x59c+i*4,actor.get(0x44+i*4));
 vm.put(0x50,0);
 if(anm_step(vm,static_cast<AnmWorld&>(world))==-2||!world.instances.registry.insert(vm,self,false,true,handle)||!world.synchronize_resources())return false;
 auto found=world.find(handle);if(!found.data)return false;
 for(u32 i=0;i<3;++i)found.put(0x59c+i*4,actor.get(0x44+i*4));
 const float angle=command.float_argument(2,host);if(command.failed)return false;
 found.put(0x18,found.get(0x18)|4u);found.put(0x50,word(angle));return true;
}
}
