#include "PlayerShotImpact.hpp"

namespace th143 {
namespace {
bool offset(const PlayerShootingConfig& c,u32 token,u32 n,u32& at){
    if(token<c.self||std::uint64_t(token)+n>std::uint64_t(c.self)+PlayerState::bytes)return false;at=token-c.self;return true;
}
}
bool stop_player_shot(PlayerState& p,u32 shot,const PlayerShootingConfig& c,PlayerShotImpactHost& host,i32& damage){
    if(std::uint64_t(shot)+0xd0>PlayerState::bytes)return false;
    auto vm=host.impact_visual(p.get(shot+0x14));if(!vm.data){p.put(shot+0x14,0);return false;}
    p.put(shot+0x5c,word(.1f));
    if(const u32 callback=vm.get(0x5c4);callback&&!host.impact_animation_callback(callback,vm,1))return false;
    vm.put(0x4a0,1);p.put(shot+0x98,2);p.put(shot+0x6c,word(p.floating(shot+0x6c)*.125f));
    for(u32 i=0;i<3;++i)vm.put(0x59c+i*4,p.get(shot+0x54+i*4));
    u32 region;if(!offset(c,p.get(shot+0xc0),0x14,region))return false;p.put(region+0x10,p.get(region+0x10)&~1u);
    p.put(shot+0xc0,0);damage=signed_word(p.get(shot+0xac));return true;
}
bool impact_player_shot(PlayerState& p,PlayerShotData& sht,u32 region,const PlayerShootingConfig& c,const PlayerShotImpactQuery& query,PlayerShotImpactHost& host,i32& damage){
    if(std::uint64_t(region)+0xa4>PlayerState::bytes)return false;u32 shot;
    if(!offset(c,p.get(region+0x98),0xd0,shot))return false;const u32 token=p.get(shot+0xbc);
    if(token<sht.token||std::uint64_t(token)+0x58>std::uint64_t(sht.token)+sht.data.size())return false;
    if(const u32 callback=sht.get(token-sht.token+0x34))return host.specialized_impact(callback,p,shot,query,damage);
    const u32 counter=p.get(shot+0x10)&2?0x184c4:0x184c0;p.put(counter,p.get(counter)+5);
    return stop_player_shot(p,shot,c,host,damage);
}
}
