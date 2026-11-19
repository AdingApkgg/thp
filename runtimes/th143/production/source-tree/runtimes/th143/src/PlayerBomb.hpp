#pragma once
#include "PlayerEquipment.hpp"
#include "CheatAnimation.hpp"
namespace th143 {
struct PlayerBombGlobals {u32 fresh=0,secondary=0;};
struct PlayerBombHost:AnmTimerHost {
    virtual bool bomb_option_busy(u32 token,bool&)=0;
    virtual bool bomb_alternate_release()=0;
    virtual bool bomb_sound(u32 id,float x)=0;
    virtual bool bomb_stop_sound(u32 id)=0;
    virtual bool bomb_bullets(AnmView position,float radius)=0; //417540,kind0
    virtual bool bomb_lasers(AnmView position,float radius)=0; //439490,kind0/noitems
};
//45b7d0 primary5. Draw45bce0 is a literal return0; its visuals live in ANM.
bool update_player_bomb(AnmView,AnmView equipment,PlayerState*,AnmView cheat,PlayerBombGlobals&,AnmWorld&,PlayerBombHost&);
}
