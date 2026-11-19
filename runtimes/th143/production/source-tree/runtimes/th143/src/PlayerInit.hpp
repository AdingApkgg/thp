#pragma once
#include "PlayerState.hpp"
#include <vector>

namespace th143 {
// Private SHT bytes become owned mutable storage; addresses remain guest tokens.
struct PlayerShotData {
    std::vector<u8> data;
    u32 token=0;
    u32 get(u32 at) const {u32 v;std::memcpy(&v,data.data()+at,4);return v;}
    void put(u32 at,u32 v){std::memcpy(data.data()+at,&v,4);}
    float floating(u32 at)const{return real(get(at));}
    bool load(const u8*,u32 bytes,u32 base,u32 collision_callback=0);
};
struct PlayerInitHost {
    virtual ~PlayerInitHost()=default;
    virtual bool bind_initial_visual(PlayerState&)=0;
};
struct PlayerInitConfig {
    u32 self=0x6a000000,resource=0,update_callback=0,draw_callback=0,rate=0x4e40b0;
};
struct PlayerPower {u32 maximum=0,step=0;};
// Original44bba0 constructor, then44bd00 after resource/SHT/callback ownership.
void player_construct(PlayerState&);
bool player_initialize(PlayerState&,PlayerShotData&,const PlayerInitConfig&,PlayerPower&,PlayerInitHost&);
}
