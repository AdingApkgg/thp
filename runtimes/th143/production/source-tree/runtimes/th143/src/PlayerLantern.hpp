#pragma once
#include "PlayerBomb.hpp"
#include "SoundQueue.hpp"
namespace th143 {
struct PlayerLanternHost:PlayerBombHost {
    virtual bool lantern_resource(u32& resource)=0; //EnemyManager+A8,enemy.anm
    virtual bool lantern_pan(i32 value)=0; //sound84 buffer virtual+40
    virtual bool lantern_countdown(const std::array<float,3>&,double)=0; //"%.2f"
};
bool update_player_lantern(AnmView,AnmView equipment,PlayerState*,AnmView cheat,PlayerBombGlobals&,SoundQueue&,AnmWorld&,PlayerLanternHost&); //45a410
bool draw_player_lantern(AnmView,PlayerState*,AnmView ascii,PlayerLanternHost&); //45acf0
}
