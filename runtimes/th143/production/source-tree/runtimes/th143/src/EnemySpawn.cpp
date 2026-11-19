#include "EnemySpawn.hpp"
#include <cstring>

namespace th143 {
i32 enemy_spawn_command(Vm& vm, VmHost& host, const Emitters& source, u32 parent,
                       const SpawnLimits& limits, EnemySpawner& world) {
    const u16 op = vm.instruction->opcode;
    const bool relative = op == 300 || op == 304 || op == 309 || op == 311 || op == 321;
    const bool restricted = op >= 309 && op <= 312;
    if (!(relative || op == 301 || op == 305 || op == 310 || op == 312)) return -2;
    if (restricted && limits.restricted != 0) return 0;
    if (limits.current >= limits.capacity) return 0;
    const u32 string_bytes = vm.instruction->argument(0);
    if (string_bytes > vm.instruction->length || string_bytes % 4) return -2;
    const u32 first = (string_bytes + 4) / 4;
    if (16 + (first + 5) * 4 > vm.instruction->length) return -2;
    const char* name = reinterpret_cast<const char*>(vm.instruction) + 20;
    if (!std::memchr(name, 0, string_bytes)) return -2;
    EnemySpawn result;
    result.position[0] = vm.float_operand(vm.instruction->argument(first), 1, host);
    result.position[1] = vm.float_operand(vm.instruction->argument(first + 1), 2, host);
    if (relative) {
        result.position[0] += source.floating(0x44);
        result.position[1] += source.floating(0x48);
    }
    result.mirrored = op == 304 || op == 305 || op == 311 || op == 312;
    if (source.get(0x4100) & 0x80000) {
        result.position[0] *= -1.f;
        result.mirrored ^= 1;
    }
    result.health = vm.integer_operand(vm.instruction->argument(first + 2), 3, host);
    result.score = vm.integer_operand(vm.instruction->argument(first + 3), 4, host);
    result.drop = vm.integer_operand(vm.instruction->argument(first + 4), 5, host);
    for (u32 i = 0; i < 12; ++i) result.inherited[i] = source.get(0x32c + i * 4);
    result.parent = parent;
    if (vm.failed) return -2;
    return world.spawn_enemy(name, result) ? 0 : -2;
}
}
