#pragma once
#include "PlayerEquipment.hpp"
#include "CheatAnimation.hpp"
namespace th143 {
struct PlayerCloakGlobals {u32 held=0,fresh=0,secondary=0;};
struct PlayerCloakHost:AnmTimerHost {
    virtual bool cloak_option_view(u32 token,AnmView&)=0;
    virtual bool cloak_option_busy(u32 token,bool&)=0;
    virtual bool cloak_alternate_release()=0; //4508e0, secondary5 cancellation
    virtual bool cloak_sound(u32 id,float x)=0;
    virtual bool cloak_countdown(const std::array<float,3>&,double seconds)=0; //40b7c0,"%.2f"
};
//457680(primary0),457d50(secondary0). Resource factories, UI child signals,
// active player flags and both clocks execute here; audio and other options
// are supplied by the session. Secondary0 requires a live primary as original.
bool update_player_cloak(AnmView option,bool secondary,AnmView equipment,PlayerState&,AnmView cheat,PlayerCloakGlobals&,AnmWorld&,PlayerCloakHost&);
bool draw_player_cloak(AnmView option,PlayerState&,AnmView ascii,PlayerCloakHost&); //457b10/4581b0
}
