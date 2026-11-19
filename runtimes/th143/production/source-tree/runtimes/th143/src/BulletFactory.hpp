#pragma once
#include "BulletPattern.hpp"
#include "BulletPool.hpp"
#include "BulletMotion.hpp"
#include "AnmVm.hpp"

namespace th143 {
struct BulletFactoryHost : BulletMotionHost, AnmVmHost {
    virtual bool player_position(float& x, float& y) = 0;
    virtual bool aim_position(float& x, float& y) { return player_position(x, y); }
    virtual bool launch_sound(i32 id, float x) { return false; }
};
// Original413b30 full factory. Return0 created,1 pool empty,-1 proximity-rejected,
// -2 unsupported service/transform. Native table data is a read-only host input.
// The factory preserves fields that the original leaves in a reused slot.
i32 bullet_create(BulletPool&, const u8* emitter, i32 inner, i32 outer, float aim,
                  Rng& gameplay_rng, BulletFactoryHost&, u32& bullet_token);
struct BulletLaunchResult { u32 attempts = 0, created = 0, rejected = 0; bool exhausted = false; float aim = 0; };
// 415660 selects the target, computes the aim, iterates signed counts, stops
// only on pool exhaustion and queues the optional spatial shot sound.
bool bullet_launch(BulletPool&, const u8* emitter, Rng&, BulletFactoryHost&, BulletLaunchResult&);
}
