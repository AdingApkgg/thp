#pragma once
#include "EclVm.hpp"

namespace th143 {
struct BulletView {
    u8* data;
    u32 get(u32 at) const { u32 v; std::memcpy(&v, data + at, 4); return v; }
    void put(u32 at, u32 v) { std::memcpy(data + at, &v, 4); }
    float floating(u32 at) const { return real(get(at)); }
    u16 state() const { return u16(get(0xc0c) >> 16); }
    void state(u16 v) { put(0xc0c, (get(0xc0c) & 65535) | (u32(v) << 16)); }
};
struct BulletMotionHost {
    virtual ~BulletMotionHost() = default;
    virtual bool timer_rate(u32 token, float& rate) = 0;
    virtual bool sprite_dimensions(u32 token, float& width, float& height) = 0;
    // Return -2 when the service is unavailable. Collision must implement
    // native 4131a0 side effects, including hit/graze and animation changes.
    virtual i32 collision(BulletView, bool forced) = 0;
    virtual i32 animate(BulletView, u32 slot) = 0;
    virtual void retire(BulletView) = 0;
    virtual bool cancellation_effect(BulletView) { return false; }
    virtual bool interrupt(BulletView b, u32 slot, i32 id) {
        const u32 vm = slot ? 0x5f4 : 0x28;
        if (b.get(vm + 0x5c4)) return false;
        b.put(vm + 0x4a0, u32(id)); return true;
    }
};
// TH143 412a70. Appearance/fast-shot transforms are connected; other transform
// types and slowdown interpolation reject explicitly. The host supplies actual
// collision/ANM/pool services rather than guessed outcomes.
i32 bullet_step(BulletView, float elapsed, BulletMotionHost&);
}
