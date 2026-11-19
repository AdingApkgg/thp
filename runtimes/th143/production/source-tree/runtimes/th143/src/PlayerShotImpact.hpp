#pragma once
#include "PlayerShooting.hpp"

namespace th143 {
struct PlayerShotImpactQuery {
    std::array<float,3> position{};
    std::array<float,2> size{};
    bool rectangle=false;
    float angle=0,radius=0;
    u32 owner=0,id=0;
};
struct PlayerShotImpactHost {
    virtual ~PlayerShotImpactHost()=default;
    virtual AnmView impact_visual(u32 handle)=0;
    virtual bool impact_animation_callback(u32 entry,AnmView,i32 signal)=0;
    virtual bool specialized_impact(u32 entry,PlayerState&,u32 shot,const PlayerShotImpactQuery&,i32& damage)=0;
};
// Original451950. Fading state2 stays in ordinary shot updates;451500 later
// recycles the slot when its VM disappears or its quad crosses the bounds.
bool stop_player_shot(PlayerState&,u32 shot,const PlayerShootingConfig&,PlayerShotImpactHost&,i32& damage);
// Original4518e0 collision-bank callback; specialized SHT +34 callbacks are
// explicit services, while ordinary pl00a uses the default path below.
bool impact_player_shot(PlayerState&,PlayerShotData&,u32 region,const PlayerShootingConfig&,const PlayerShotImpactQuery&,PlayerShotImpactHost&,i32& damage);
}
