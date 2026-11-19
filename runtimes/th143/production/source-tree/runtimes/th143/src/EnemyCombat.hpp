#pragma once
#include "EnemyActorRuntime.hpp"
#include "EnemyContact.hpp"
#include "EnemyDeath.hpp"
#include "EclProgram.hpp"
namespace th143 {
struct EnemyCombatState {
    AnmWorld& graphics;
    EclProgram& program;
    PlayerState& player;
    PlayerShotData& shots;
    PlayerShootingConfig& shooting;
    PlayerShotContactGlobals& shot_globals;
    PlayerShotContactHost& shot_services;
    EnemyContactGlobals& enemy_globals;
    ItemPool& items;
    Rng& gameplay_rng;
};
struct EnemyCombatServices {
    virtual ~EnemyCombatServices()=default;
    virtual bool sound(i32,float)=0;
    virtual bool resource(i32,u32&)=0;
    virtual void frame_rate(float){}
    virtual bool visual_script(AnmView,i32){return false;}
    virtual bool actor_callback(u32,ActorState&,i32&){return false;}
    virtual bool damage_callback(u32,ActorState&,i32,i32&){return false;}
    virtual bool body_callback(u32,ActorState&){return false;}
    virtual bool death_callback(u32,ActorState&,EclOwner&){return false;}
    virtual bool auxiliary_update(ActorState&){return false;}
    virtual bool body_circle(const std::array<float,3>&,float,i32&){return false;}
    virtual bool body_rectangle(const std::array<float,3>&,float,float,float,i32&){return false;}
    virtual bool body_graze(){return false;}
};
// Joins shot contacts, health/phase scripts and death/drop ownership. Actor
// traversal and removal remain in EnemyScripts, including its saved-next rule.
class EnemyCombat final:public EnemyActorRuntime,private EnemyContactHost,private EnemyDeathHost {
public:
    EnemyCombat(EnemyCombatState state,EnemyCombatServices& services):state(state),services(services){}
    void begin_frame()override;
    float current_rate()const override{return state.graphics.rate;}
    float exchange_rate(float)override;
    bool slowdown(ActorState&,float)override;
    bool update_actor(ActorState&,EclOwner&,u32,float,i32&)override;
    bool retire_actor(ActorState&,EclOwner&)override;
private:
    EnemyCombatState state;
    EnemyCombatServices& services;
    EclOwner* owner=nullptr;
    u32 owner_callback=0;
    float elapsed=1;
    bool timer_rate(u32,float&)override;
    u32 global_rate_token()const override;
    AnmView enemy_visual(u32)override;
    bool enemy_visual_script(AnmView,i32)override;
    bool incoming_shots(const PlayerShotImpactQuery&,PlayerShotContactResult&)override;
    bool damage_callback(u32,ActorState&,i32,i32&)override;
    bool phase_script(ActorState&,u32,bool,i32&)override;
    bool enemy_death(ActorState&,i32&)override;
    bool body_callback(u32,ActorState&)override;
    bool body_circle(const std::array<float,3>&,float,i32&)override;
    bool body_rectangle(const std::array<float,3>&,float,float,float,i32&)override;
    bool body_graze()override;
    bool enemy_sound(i32,float)override;
    bool death_sound(i32,float)override;
    bool death_resource(i32,u32&)override;
    bool death_script_name(u32,const char*&)override;
    bool death_callback(u32,ActorState&,EclOwner&)override;
};
}
