#include "EnemyManagerSweep.hpp"
#include <map>
namespace th143 {
namespace {std::map<EnemyScripts*,EnemyManagerSweepService*> services;}
void bind_enemy_manager_sweep(EnemyScripts& scripts,EnemyManagerSweepService* service){if(service)services[&scripts]=service;else services.erase(&scripts);}
bool dispatch_enemy_manager_sweep(EnemyScripts& scripts){auto at=services.find(&scripts);return at!=services.end()&&at->second->sweep();}
bool sweep_enemy_manager(u32 manager,EnemyManagerSweepHost& host){
    auto read=[&](u32 p,u32& value){return host.enemy_cancel_read(p,&value,4);};auto write=[&](u32 p,u32 value){return host.enemy_cancel_write(p,&value,4);};
    u32 node;if(!read(manager+0xd0,node))return false;
    for(u32 budget=100000;node;){if(!budget--)return false;u32 actor,next,flags;if(!read(node+4,next)||!read(node,actor)||!read(actor+0x52f0,flags))return false;
        if(!((flags&0xa0)||(flags&0xc00400))||(flags&0x100)){
            std::array<u8,0x48> zero{};if(!host.enemy_cancel_write(actor+0x5224,zero.data(),zero.size())||!write(actor+0x5264,0x42000000)||!write(actor+0x5268,0x42000000))return false;
            i32 ignored;if(!host.enemy_cancel_death(actor,ignored)||!read(actor+0x52f0,flags)||!write(actor+0x52f0,flags|0x2000000))return false;
        }node=next;
    }
    u32 old,token,fraction;if(!read(manager+0xbc,old)||!read(manager+0xc4,token)||!read(manager+0xc0,fraction)||!write(manager+0xb8,old))return false;
    float rate=1;if(token&&!host.timer_rate(token,rate))return false;const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));const float value=real(fraction)+(unit?1.f:rate);const u32 count=unit?old+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000;
    return write(manager+0xbc,count)&&write(manager+0xc0,word(value));
}
}
