#pragma once
#include "PlayerBomb.hpp"
namespace th143 {
struct PlayerDecoyHost:PlayerBombHost {
    virtual bool decoy_countdown(const std::array<float,3>&,double seconds)=0; //40b7c0,"%.2fs"
};
bool update_player_decoy(AnmView,AnmView equipment,PlayerState*,AnmView cheat,PlayerBombGlobals&,AnmWorld&,PlayerDecoyHost&); //45c550
bool draw_player_decoy(AnmView,AnmView ascii,PlayerDecoyHost&); //45c980
}
