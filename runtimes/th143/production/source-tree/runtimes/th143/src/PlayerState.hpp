#pragma once
#include "EclVm.hpp"
#include <array>

namespace th143 {
// TH143's player object. Resource and callback words are opaque tokens until
// resolved by their owning services; portable code never dereferences them.
struct PlayerState {
    static constexpr u32 bytes = 0x184cc;
    std::array<u8, bytes> data{};
    u32 get(u32 at) const { u32 value; std::memcpy(&value, data.data() + at, 4); return value; }
    void put(u32 at, u32 value) { std::memcpy(data.data() + at, &value, 4); }
    float floating(u32 at) const { return real(get(at)); }
};
struct PlayerHitHost {
    virtual ~PlayerHitHost() = default;
    virtual bool hit(PlayerState&) = 0;
};
}
