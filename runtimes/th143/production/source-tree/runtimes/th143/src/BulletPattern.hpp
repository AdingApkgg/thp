#pragma once
#include "EclVm.hpp"
#include "Rng.hpp"

namespace th143 {
struct BulletDirection {
    float speed = 0, angle = 0;
    // Native factory keeps XMM3 before wrapping the stored angle. Its first
    // velocity vector uses this value; later updates use the stored angle.
    float raw_angle = 0;
};
// Original 413bb3..413d1f, including the out-of-line pattern branches.
// Descriptor is one 0x380-byte emitter record. Patterns 11/12 still require
// the separately verified original trigonometric implementation.
bool bullet_pattern(const u8* descriptor, i32 inner, i32 outer, float aim,
                    Rng&, BulletDirection&);
}
