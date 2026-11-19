#pragma once
#include "AnmState.hpp"
namespace th143 {
struct EnemyAnimationSignalHost {virtual ~EnemyAnimationSignalHost()=default;virtual bool enemy_animation_signal(u32 handle,i32 signal)=0;};
// ECL317/4228e7: the signal is sign-extended from its low16 bits.
i32 enemy_animation_signal_command(AnmView,Vm&,VmHost&,EnemyAnimationSignalHost&);
}
