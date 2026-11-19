#pragma once
#include "PlayerShotImpact.hpp"
namespace th143 {
struct PlayerShotContactGlobals {u32 score=0;bool cheat_active=false;};
struct PlayerShotContactOptions {bool hit_flag=true,last_position=true;};
struct PlayerShotContactResult {i32 damage=0;u32 hit_flag=0;std::array<float,3> last_position{};};
struct PlayerShotContactHost:PlayerShotImpactHost {
    virtual bool cheat_damage(const PlayerShotImpactQuery&,i32& damage)=0;
    virtual bool area_callback(u32 entry,PlayerState&,u32 region,const PlayerShotImpactQuery&,i32& damage)=0;
};
// Original4515b0. Optional output fields retain their caller bytes when no
// write occurs, including the early return for an unchanged player timer.
bool contact_player_shots(PlayerState&,PlayerShotData&,const PlayerShootingConfig&,PlayerShotContactGlobals&,
                          const PlayerShotImpactQuery&,const PlayerShotContactOptions&,PlayerShotContactHost&,PlayerShotContactResult&);
}
