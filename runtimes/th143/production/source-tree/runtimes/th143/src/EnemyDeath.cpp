#include "EnemyDeath.hpp"
#include <cmath>
namespace th143 {
namespace {
bool death_visual(AnmWorld& world,u32 token,i32 script,const std::array<float,3>& pos,float angle){
    auto* resource=world.resource(token);if(!resource||script<0||u32(script)>=resource->templates.size())return false;
    ++world.instances.resource_uses[token];u32 self;AnmView vm;if(!world.acquire_state(self,vm))return false;
    anm_copy_template(vm,self,{resource->templates[script].data()},world.global_rate_token());
    vm.put(0x1c,(vm.get(0x1c)&~0x40000u)|0x20200);vm.put(0x24,3);
    for(u32 i=0;i<3;++i)vm.put(0x59c+i*4,word(pos[i]));vm.put(0x50,word(angle));
    if(anm_step(vm,world)==-2){u16 opcode=0;world.read(vm.get(0x28),&opcode,2);world.error=opcode;return false;}u32 handle;return world.instances.registry.insert(vm,self,false,false,handle);
}
}
bool enemy_death(ActorState& s,EclOwner& owner,u32 callback,AnmWorld& graphics,ItemPool& items,Rng& rng,EnemyDeathHost& host,i32& result){
    result=0;const std::array<float,3> position{s.fields.floating(0x44),s.fields.floating(0x48),s.fields.floating(0x4c)};
    const i32 sound=signed_word(s.get(0x4080));if(sound>=0&&!host.death_sound(sound,position[0]))return false;
    const i32 script=signed_word(s.get(0x4084));
    if(script>=0){
        const float dx=s.fields.floating(0x320)-position[0],dy=s.fields.floating(0x324)-position[1];float angle=real(0xbfc90fdb);
        if(!(real(0x3d23d70b)>dy*dy+dx*dx))angle=float(std::atan2(double(position[1]-s.fields.floating(0x324)),double(position[0]-s.fields.floating(0x320))));
        u32 resource;if(!host.death_resource(signed_word(s.get(0x4088)),resource)||!death_visual(graphics,resource,script,position,angle))return false;
    }
    if(const u32 type=s.get(0x4034)){
        items.put(0xde21d8,items.get(0xde21d8)+1);
        if(signed_word(type)>=13){u32 token;if(!items.spawn_delayed(signed_word(type),position,real(0xbfc90fdb),real(0x3fe66666),graphics.global_rate_token(),token))return false;}
    }
    if(!enemy_drops({s.fields.data.data()+0x4034},position,rng,items,graphics.global_rate_token()))return false;s.put(0x4034,0);
    if(const u32 name_token=s.get(0x41d4)){
        const char* name;if(!host.death_script_name(name_token,name))return false;i32 ignored;if(!restart_enemy_phase(owner,name,true,0.f,ignored))return false;s.put(0x41d4,0);
    }
    if(callback&&!host.death_callback(callback,s,owner))return false;result=1;return true;
}
}
