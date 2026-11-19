#pragma once
#include "AnmVm.hpp"

namespace th143 {
struct AnmEffect7Host : AnmTimerHost {
    virtual AnmView find(u32 handle)=0;
    virtual bool create(i32 script,u32& handle)=0;
    virtual Rng& rng()=0;
    virtual bool slowdown(AnmView root,float& value)=0;
};
// Original407670: four births per distinct counter below50, two Hermite
// trajectory phases, color inheritance and persistent200-handle bookkeeping.
i32 anm_effect7_step(AnmView root,u8* data,AnmEffect7Host&);
// Original4081f0 clears all live particle scripts;408230 signal1 advances300.
bool anm_effect7_cancel(u8* data,AnmEffect7Host&);
bool anm_effect7_signal(u8* data,i32 signal,AnmEffect7Host&);
}
