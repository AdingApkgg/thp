#include "BulletPattern.hpp"

namespace th143 {
namespace {
float value(const u8* p, u32 at) { u32 v; std::memcpy(&v, p + at, 4); return real(v); }
i32 count(const u8* p, u32 at) { std::int16_t v; std::memcpy(&v, p + at, 2); return v; }
float normalize(float angle) {
    const float pi = real(0x40490fdb), tau = real(0x40c90fdb);
    // The original applies two bounded reductions. Each pair shares one
    // counter; its limit tests the previous value after doing the reduction.
    for (u32 pass = 0; pass < 2; ++pass) {
        u32 steps = 0;
        while (angle > pi) { angle -= tau; if (steps++ > 32) break; }
        while (-pi > angle) { angle += tau; if (steps++ > 32) break; }
    }
    return angle;
}
}
bool bullet_pattern(const u8* descriptor, i32 inner, i32 outer, float aim,
                    Rng& rng, BulletDirection& result) {
    const i32 columns = count(descriptor, 0x364), rows = count(descriptor, 0x366);
    const i32 mode = count(descriptor, 0x368);
    if (mode < 0 || mode > 10 || columns <= 0 || rows <= 0 ||
        inner < 0 || inner >= columns || outer < 0 || outer >= rows) return false;
    const float base = value(descriptor, 0x14), step = value(descriptor, 0x18);
    const float first = value(descriptor, 0x1c), last = value(descriptor, 0x20);
    const float pi = real(0x40490fdb), tau = real(0x40c90fdb);
    float speed = first, angle = 0.f;
    if (rows > 1) speed -= (first - last) * float(outer) / float(rows - 1);
    switch (mode) {
    case 0: case 1: {
        float offset = columns & 1 ? float((inner + 1) / 2) * step
                                  : float(inner / 2) * step + step * .5f;
        offset += 0.f;
        if (inner & 1) offset *= -1.f;
        if (mode == 0) offset += aim;
        angle = base + offset;
        break;
    }
    case 2: case 3: case 4: case 5: {
        angle = (mode == 2 || mode == 4) ? aim + 0.f : 0.f;
        const float spoke = float(inner) * tau / float(columns);
        if (mode == 4 || mode == 5) angle += pi / float(columns);
        angle += spoke;
        const float row_angle = float(outer) * step + base;
        angle += row_angle;
        break;
    }
    case 6:
        angle = base + rng.signed_unit() * step;
        break;
    case 7:
        speed = rng.unit() * last + first;
        angle = float(inner) * tau / float(columns) + 0.f;
        angle += float(outer) * step + base;
        break;
    case 8:
        angle = base + rng.signed_unit() * step;
        speed = rng.unit() * last + first;
        break;
    case 9: case 10: {
        const float spoke = float(inner) * tau / float(columns);
        float offset;
        if (rows & 1) {
            offset = float((outer + 1) / 2) * step + spoke;
            if (rows > 1) speed = (last - first) * float((outer + 1) & ~1) / float(rows - 1) + first;
        } else {
            offset = float(outer / 2) * step + step * .5f + spoke;
            if (rows > 1) speed = (last - first) * float(outer & ~1) / float(rows - 1) + first;
        }
        if (outer & 1) offset *= -1.f;
        if (mode == 9) offset += aim;
        angle = base + offset;
        break;
    }
    }
    result.speed = speed;
    result.raw_angle = angle;
    result.angle = normalize(angle + 0.f);
    return true;
}
}
