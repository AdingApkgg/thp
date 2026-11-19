#include "ActorControls.hpp"

namespace th143 {
i32 actor_control_command(Vm& vm, VmHost& host, ActorState& state,
                          ActorControlWorld& world, u32 actor_token, u32 rate_token) {
    const u32 op = vm.instruction->opcode;
    switch (op) {
    case 302:
        state.put(0x304, u32(vm.integer_argument(0, host)));
        break;
    case 500: case 501: case 508: {
        const u32 offset = op == 500 ? 0x110 : op == 501 ? 0x118 : 0x4074;
        state.put(offset, word(vm.float_argument(0, host)));
        state.put(offset + 4, word(vm.float_argument(1, host)));
        break;
    }
    case 506:
        for (u32 offset = 0x4038; offset < 0x4074; offset += 4) state.put(offset, 0);
        break;
    case 507: {
        const i32 slot = vm.integer_argument(0, host);
        const u32 value = u32(vm.integer_argument(1, host));
        if (slot < 0 || slot >= 16) return -2;
        state.put(0x4034 + u32(slot) * 4, value);
        break;
    }
    case 510:
        state.put(0x4034, u32(vm.integer_argument(0, host)));
        break;
    case 511: {
        const u32 health = u32(vm.integer_argument(0, host));
        for (u32 offset : {0x4018u, 0x401cu, 0x4020u}) state.put(offset, health);
        if (state.get(0x4100) & 0x800000) state.put(0x4100, state.get(0x4100) | 0x40000000);
        state.put(0x4024, health * 7u);
        break;
    }
    case 512: {
        const i32 slot = vm.integer_argument(0, host);
        world.flags &= ~1u;
        if (slot < 0) {
            if (state.get(0x4100) & 0x800000) {
                const i32 previous = signed_word(state.get(0x4110));
                if (previous < 0 || previous >= 16) return -2;
                world.bosses[u32(previous)] = 0;
            }
            state.put(0x4100, state.get(0x4100) & ~0x800000u);
        } else {
            if (slot >= 16) return -2;
            state.put(0x4100, state.get(0x4100) | 0x800000);
            world.bosses[u32(slot)] = actor_token;
            state.put(0x4110, u32(slot));
        }
        break;
    }
    case 515: {
        const u32 value = u32(vm.integer_argument(0, host));
        if (!(state.get(0x40a8) & 1)) {
            state.put(0x40a4, rate_token);
            state.put(0x40a8, state.get(0x40a8) | 1);
        }
        state.put(0x4098, value - 1);
        state.put(0x409c, value);
        state.put(0x40a0, word(float(signed_word(value))));
        break;
    }
    default: return -2;
    }
    return vm.failed ? -2 : 0;
}
}
