#pragma once
#include "PlayerBomb.hpp"
namespace th143 {
struct PlayerOrbGlobals : PlayerBombGlobals {u32 held=0;};
struct PlayerOrbHost : PlayerBombHost {
    // EnemyManager+5c actor position1234; no actor yields(0,192,0).
    virtual bool orb_target(std::array<float,3>&)=0;
};
//45af40 primary4. Draw45b730 is a literal return0.
bool update_player_orb(AnmView,AnmView equipment,PlayerState*,AnmView cheat,PlayerOrbGlobals&,AnmWorld&,PlayerOrbHost&);
}
