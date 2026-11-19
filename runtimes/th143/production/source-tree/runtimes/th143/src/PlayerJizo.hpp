#pragma once
#include "PlayerEquipment.hpp"
#include "CheatAnimation.hpp"
namespace th143 {
struct PlayerJizoHost:AnmTimerHost {
    virtual bool jizo_alternate_release()=0;
    virtual bool jizo_sound(u32 id,float x)=0;
    virtual bool jizo_remaining(const std::array<float,3>&,i32 count)=0; //40b7c0,"&   %d"
};
struct PlayerJizoDrawState {u32 flags=0;std::array<u32,3> position{};};
bool update_player_jizo(AnmView option,bool secondary,AnmView equipment,PlayerState*,AnmView cheat,AnmWorld&,PlayerJizoHost&); //45bd70/45c140
bool draw_player_jizo(AnmView option,bool secondary,PlayerState*,AnmView ascii,PlayerJizoDrawState&,PlayerJizoHost&); //45bfc0/45c380
}
