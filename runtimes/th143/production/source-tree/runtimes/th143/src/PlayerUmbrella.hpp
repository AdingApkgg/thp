#pragma once
#include "PlayerBomb.hpp"
namespace th143 {
struct PlayerUmbrellaGlobals : PlayerBombGlobals {
    u32 held=0,primary=0;
    std::array<u32,3> neutral_velocity{}; //53b184..8c
};
struct PlayerUmbrellaHost : PlayerBombHost {virtual bool bomb_sound_unpositioned(u32 id)=0;};
//459250 primary2 /459da0 secondary2. Their draw functions return0.
bool update_player_umbrella(AnmView,bool secondary,AnmView equipment,PlayerState*,AnmView cheat,PlayerUmbrellaGlobals&,AnmWorld&,PlayerUmbrellaHost&);
}
