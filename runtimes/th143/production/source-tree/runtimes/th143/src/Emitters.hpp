#pragma once
#include "EclVm.hpp"
#include <array>

namespace th143 {
struct EmitterSink {
    virtual ~EmitterSink() = default;
    virtual bool launch(const u8* parameters, u32 bytes, u32 owner) = 0;
};
// Selected TH143 enemy-layout fields. Unknown fields are preserved, not filled
// with guessed semantics. Each 0x380-byte emitter begins at +0x63c.
struct Emitters {
    static constexpr u32 bytes = 0x41b8, stride = 0x380, count = 16;
    std::array<u8, bytes> data{};
    u32 get(u32 offset) const;
    float floating(u32 offset) const { return real(get(offset)); }
    void put(u32 offset, u32 value);
    i32 command(Vm&, VmHost&, EmitterSink* sink = nullptr);
};
}
