#pragma once
#include "Emitters.hpp"

namespace th143 {
struct EnemySpawn {
    float position[3]{};
    i32 score = 0, drop = 0, health = 0;
    u32 mirrored = 0, world_coordinates = 0;
    u32 inherited[12]{};
    u32 parent = 0;
};
static_assert(sizeof(EnemySpawn) == 0x54);
struct SpawnLimits { i32 current = 0, capacity = 99999, restricted = 0; };
struct EnemySpawner {
    virtual ~EnemySpawner() = default;
    virtual bool spawn_enemy(const char* name, const EnemySpawn&) = 0;
};
// Original 421ebe / 426db0: named 2D child spawn descriptors. The constructor
// remains the supplied world's responsibility; a missing world is an error.
i32 enemy_spawn_command(Vm&, VmHost&, const Emitters& source, u32 parent,
                       const SpawnLimits&, EnemySpawner&);
}
