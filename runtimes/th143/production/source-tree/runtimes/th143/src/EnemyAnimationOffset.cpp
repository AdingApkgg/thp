#include "EnemyAnimationOffset.hpp"
namespace th143 {
i32 enemy_animation_offset(AnmView actor, Vm& vm, VmHost& host) {
    if (vm.instruction->opcode != 320) return -2;
    const i32 slot = vm.integer_argument(0, host);
    const std::int64_t offset = 0x184 + std::int64_t(slot) * 12;
    if (vm.failed || offset < 0 || offset + 12 > 0x41b8) return -2;
    // The original has no 24-slot check: preserve all in-allocation offsets.
    const float x = vm.float_argument(1, host);
    if (vm.failed) return -2;
    actor.put(u32(offset), word(x));
    const float y = vm.float_argument(2, host);
    if (vm.failed) return -2;
    actor.put(u32(offset + 4), word(y));
    actor.put(u32(offset + 8), 0);
    return 0;
}
}
