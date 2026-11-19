#pragma once
#include "EclVm.hpp"

namespace th143 {
// Byte-compatible TH143 ANM VM. Addresses remain host tokens, never C++ pointers.
struct AnmView {
    static constexpr u32 bytes = 0x5cc;
    u8* data;
    u32 get(u32 at) const { u32 v; std::memcpy(&v, data + at, 4); return v; }
    void put(u32 at, u32 v) { std::memcpy(data + at, &v, 4); }
    float floating(u32 at) const { return real(get(at)); }
    AnmView sub(u32 at) const { return {data + at}; }
};
struct AnmTimerHost {
    virtual ~AnmTimerHost() = default;
    virtual bool timer_rate(u32 token, float& value) = 0;
    virtual u32 global_rate_token() const { return 0x4e40b0; }
};
}
