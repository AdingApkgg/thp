#include "ActorState.hpp"
#include <cstring>

namespace th143 {
u32 ActorState::get(u32 offset) const {
    if (offset < Emitters::bytes) return fields.get(offset);
    u32 v; std::memcpy(&v, tail.data() + offset - Emitters::bytes, 4); return v;
}
void ActorState::put(u32 offset, u32 value) {
    if (offset < Emitters::bytes) fields.put(offset, value);
    else std::memcpy(tail.data() + offset - Emitters::bytes, &value, 4);
}
void ActorState::initialize(u32& next_id, u32& last_id, u32 owner_token, u32 rate_token) {
    // TH143 41ee00 clears the whole state AFTER its member constructors.
    fields.data.fill(0); tail.fill(0);
    id = next_id; last_id = next_id;
    if (!++next_id) next_id = 1;
    parent = 0;
    put(0x38c, owner_token); put(0x41b8, owner_token);
    for (u32 offset : {0x110u, 0x114u, 0x118u, 0x11cu}) put(offset, word(24.f));
    put(0x4094, 0xffffffff); put(0x4110, 0xffffffff);
    put(0x4074, word(32.f)); put(0x4078, word(32.f));
    for (u32 offset : {0x35cu, 0x370u, 0x4098u, 0x40acu}) {
        put(offset, 0xffffffff); put(offset + 4, 0); put(offset + 8, 0);
        put(offset + 12, rate_token); put(offset + 16, 1);
    }
    put(0x31c, 1); put(0x40c0, 60); put(0x40c4, 1);
    for (u32 index = 0; index < 8; ++index) {
        put(0x4118 + index * 20, 0xffffffff);
        put(0x411c + index * 20, 0xffffffff);
    }
    for (u32 offset = 0x2a4; offset < 0x304; offset += 4) put(offset, 0xffffffff);
    put(0x40e0, word(1.f));
}
u8 ActorState::bind_spawn(const EnemySpawn& spawn, u32 difficulty, u32 rate_token) {
    // 41e29f..41e425 executes after construction and before first enemy update.
    for (u32 i = 0; i < 3; ++i) put(0x88 + i * 4, word(spawn.position[i]));
    put(0x4014, u32(spawn.score));
    put(0x4018, u32(spawn.health)); put(0x401c, u32(spawn.health));
    put(0x4034, u32(spawn.drop));
    u32 flags = get(0x4100);
    flags = (flags & ~0x80000u) | ((spawn.mirrored & 1) << 19);
    flags = (flags & ~0x4000000u) | ((spawn.world_coordinates & 1) << 26);
    if (spawn.health >= 1000) flags |= 0x40000000;
    put(0x4100, flags);
    for (u32 i = 0; i < 12; ++i) put(0x32c + i * 4, spawn.inherited[i]);
    put(0x4098, 1); put(0x409c, 2); put(0x40a0, word(2.f));
    put(0x40a4, rate_token); put(0x40a8, get(0x40a8) | 1);
    put(0x40e8, 0xffffffff); put(0x40ec, 0); put(0x40f0, 0);
    put(0x40f4, rate_token); put(0x40f8, get(0x40f8) | 1);
    put(0x40fc, 0); put(0x318, 0);
    parent = spawn.parent;
    return u8(1u << (difficulty & 31));
}
}
