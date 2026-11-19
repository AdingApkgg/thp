#pragma once
#include "ActorState.hpp"
#include "EnemyDrops.hpp"
#include "EnemyPhaseScript.hpp"
#include "AnmWorld.hpp"
namespace th143 {
struct EnemyDeathHost {
    virtual ~EnemyDeathHost()=default;
    virtual bool death_sound(i32 id,float x)=0;
    virtual bool death_resource(i32 slot,u32& resource)=0;
    virtual bool death_script_name(u32 token,const char*& name)=0;
    virtual bool death_callback(u32 entry,ActorState&,EclOwner&)=0;
};
// Original4215f0, including pre-step rotation/tail-inserted death graphics,
// real drop/RNG state and the zero-elapsed death script. The owner callback
// word is stored outside ActorState at native owner+11e0.
bool enemy_death(ActorState&,EclOwner&,u32 owner_callback,AnmWorld&,ItemPool&,Rng&,EnemyDeathHost&,i32& result);
}
