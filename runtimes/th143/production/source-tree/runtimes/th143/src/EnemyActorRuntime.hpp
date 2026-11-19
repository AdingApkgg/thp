#pragma once
#include "ActorState.hpp"
#include "EclOwner.hpp"
namespace th143 {
// Services used by the original4211e0/421310 actor loop. A false return
// means an unavailable operation; a nonzero result means normal retirement.
struct EnemyActorRuntime {
    virtual ~EnemyActorRuntime()=default;
    virtual void begin_frame()=0;
    virtual float current_rate()const=0;
    virtual float exchange_rate(float)=0;
    virtual bool slowdown(ActorState&,float)=0;
    virtual bool update_actor(ActorState&,EclOwner&,u32 owner_callback,float elapsed,i32& result)=0;
    virtual bool retire_actor(ActorState&,EclOwner&)=0;
};
}
