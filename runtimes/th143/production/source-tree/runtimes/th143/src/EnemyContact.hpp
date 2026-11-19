#pragma once
#include "EnemyHealth.hpp"
#include "PlayerShotContact.hpp"
namespace th143 {
struct EnemyContactGlobals {
    EnemyPhaseGlobals phase;
    u32 player_state=0,cheat_mode=0,normal_damage=0,bomb_damage=0;
    bool hud_blocked=false;
};
struct EnemyContactHost:AnmTimerHost {
    virtual AnmView enemy_visual(u32 handle)=0;
    virtual bool enemy_visual_script(AnmView,i32 script)=0;
    virtual bool incoming_shots(const PlayerShotImpactQuery&,PlayerShotContactResult&)=0;
    virtual bool damage_callback(u32 entry,ActorState&,i32 incoming,i32& additional)=0;
    // These services own script threads, instruction lookup/execution and the
    // complete death/drop lifecycle. They must reject unavailable operations.
    virtual bool phase_script(ActorState&,u32 script,bool execute_now,i32& result)=0;
    virtual bool enemy_death(ActorState&,i32& result)=0;
    virtual bool body_callback(u32 entry,ActorState&)=0;
    virtual bool body_circle(const std::array<float,3>& position,float radius,i32& result)=0;
    virtual bool body_rectangle(const std::array<float,3>& position,float width,float height,float angle,i32& result)=0;
    virtual bool body_graze()=0;
    virtual bool enemy_sound(i32 id,float x)=0;
};
// Original420400, including the two phase checks, visual flash/sounds and
// flash timer. Returns the original0/1/-1 separately from a missing service.
bool contact_enemy(ActorState&,EnemyContactGlobals&,EnemyContactHost&,i32& result);
}
