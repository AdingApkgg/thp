#include "GameOver.hpp"
#include <cmath>

namespace th143 {
bool game_statistics_time(SaveData& save,GameOverGlobals& g,GameOverHost& host){
    if(g.root_mode || g.application_state==0xffffffff || g.application_state==3)return true;
    double now;if(!g.clock.sample(host,now))return false;const double elapsed=now-g.statistics_time;
    if(elapsed>=0){
        const double amount=elapsed*100.;if(amount>=0x1p64)return false;
        auto s=save.view();std::uint64_t total=std::uint64_t(s.get(0xef94))|(std::uint64_t(s.get(0xef98))<<32);total+=std::uint64_t(amount);
        s.put(0xef94,u32(total));s.put(0xef98,u32(total>>32));
        if(total>=360000&&!host.achievement(14))return false;
        if(total>=1800000&&!host.achievement(15))return false;
        if(total>=3600000&&!host.achievement(16))return false;
    }
    if(!g.clock.sample(host,now))return false;g.statistics_time=now;return true;
}
bool game_over(PauseMenu& menu,SaveData& save,GameOverGlobals& g,AnmWorld& world,AnmOverlay& overlay,u32 reason,GameOverHost& host){
    if(!game_statistics_time(save,g,host))return false;
    auto s=save.view(),m=menu.view();
    if(!g.root_mode&&signed_word(s.get(0xf07c))<99999999){
        const u32 deaths=s.get(0xf07c)+1;s.put(0xf07c,deaths);
        const u32 achievement=deaths==100?17:deaths==200?18:deaths==300?19:0;
        if(achievement&&!host.achievement(achievement))return false;
    }
    m.put(0x91b0,reason);
    if(g.root_mode==1){g.application_state=(g.config&0x2000)?2:4;return true;}
    menu.state(2);m.put(0x10,0xffffffff);m.put(0x14,0);m.put(0x18,0);
    if(!(m.get(0x34)&1)){m.put(0x30,world.global_rate_token());m.put(0x34,m.get(0x34)|1);}
    m.put(0x24,0xffffffff);m.put(0x28,0);m.put(0x2c,0);m.put(0x10c,0);g.root_flags|=0x10;
    if(!host.pause_audio()||!host.sound_and_flush(14))return false;
    m.put(0x91bc,m.get(0x91bc)|1);u32 handle;
    world.rate=g.rate;if(!overlay.create(world,g.text_resource,58,nullptr,0,-1,4,handle))return false;m.put(0x1ec,handle);
    m.put(0x91c0,g.front_resource);m.put(0x1f4,0);m.put(0x2d8,word(g.rate));g.rate=1;world.rate=1;
    m.put(0x200,g.presentation);g.presentation=1;
    if((g.game_flags&0xc00)!=0xc00)for(u32 i=0;i<3;++i){if(!overlay.create(world,g.front_resource,227+i,nullptr,0,-1,4,handle))return false;m.put(0x3f8+i*4,handle);}
    return true;
}
}
