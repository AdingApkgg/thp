#pragma once
#include "ActorState.hpp"

namespace th143 {
struct ActorControlWorld {
    std::array<u32, 16> bosses{};
    u32 flags = 0;
};
// TH143 scalar controls and boss registration. Native pointers in the boss
// registry are represented by the caller's stable actor token.
i32 actor_control_command(Vm&, VmHost&, ActorState&, ActorControlWorld&,
                          u32 actor_token, u32 rate_token);
}
