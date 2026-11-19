#pragma once
#include <cstdint>

namespace th143 {
// TH143 1.00a: 4035a0, 403610/4036a0, 403730, 403770/4037b0/4037f0.
// Synchronization is a host concern; this models a single owner's RNG state.
struct Rng {
    std::uint16_t seed = 0, reserved = 0;
    std::uint32_t calls = 0;

    std::uint16_t next16() noexcept {
        const auto mixed = std::uint16_t((seed ^ 0x9630u) - 0x6553u);
        seed = std::uint16_t((mixed << 2) | (mixed >> 14));
        ++calls;
        return seed;
    }
    std::uint32_t next32() noexcept {
        // The returned halves are the words BEFORE rotation, unlike next16().
        const auto high = std::uint16_t((seed ^ 0x9630u) - 0x6553u);
        const auto middle = std::uint16_t((high << 2) | (high >> 14));
        const auto low = std::uint16_t((middle ^ 0x9630u) - 0x6553u);
        seed = std::uint16_t((low << 2) | (low >> 14));
        calls += 2;
        return (std::uint32_t(high) << 16) | low;
    }
    std::uint32_t next_four() noexcept {
        const auto low = next16(), high = next16();
        next16();
        next16();
        return (std::uint32_t(high) << 16) | low;
    }
    // Native converts the unsigned result to float BEFORE the SSE operation.
    float unit() noexcept { return float(next32()) * 0x1p-32f; }
    float signed_unit() noexcept { return float(float(next32()) * 0x1p-31f) - 1.f; }
    float angle() noexcept {
        // Constants' exact float words in TH143: 4e22f983 and 40490fdb.
        return float(float(next32()) / 683565248.f) - 0x1.921fb6p+1f;
    }
};
static_assert(sizeof(Rng) == 8);
}
