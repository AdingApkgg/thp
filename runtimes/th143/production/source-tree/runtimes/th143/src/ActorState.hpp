#pragma once
#include "EnemySpawn.hpp"

namespace th143 {
// The enemy's gameplay block follows its script owner at native +11f0.
// Pointer words use explicit owner/rate tokens; portable code resolves these
// through its owning actor/world rather than dereferencing native addresses.
struct ActorState {
    static constexpr u32 bytes = 0x41e8;
    Emitters fields;
    std::array<u8, bytes - Emitters::bytes> tail{};
    u32 id = 0, parent = 0;
    u32 get(u32 offset) const;
    void put(u32 offset, u32 value);
    void initialize(u32& next_id, u32& last_id, u32 owner_token, u32 rate_token);
    u8 bind_spawn(const EnemySpawn&, u32 difficulty, u32 rate_token);
};
}
