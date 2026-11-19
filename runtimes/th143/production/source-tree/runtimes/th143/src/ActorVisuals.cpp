#include "ActorVisuals.hpp"

namespace th143 {
i32 actor_visual_command(Vm& vm, VmHost& host, ActorState& state, AnmHandles& animations) {
    const u32 op = vm.instruction->opcode;
    if (op != 502 && op != 503) return -2;
    const u32 operand = u32(vm.integer_argument(0, host));
    u32 flags = state.get(0x4100);
    flags = op == 502 ? flags | operand : flags & ~operand;
    state.put(0x4100, flags);
    if (op == 502 ? (flags & 0x20) != 0 : (flags & 0x20) == 0)
        for (u32 slot = 0; slot < 24; ++slot) animations.flag2(state.get(0x124 + slot * 4), op == 503);
    return vm.failed ? -2 : 0;
}
}
