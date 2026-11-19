#include "BulletLifetimeTransform.hpp"
#include "BulletScaleTransform.hpp"
#include "BulletEnemyTransform.hpp"
#include "BulletTimedFreeze.hpp"
#include "BulletOffscreenGrace.hpp"
#include "BulletSoundTransform.hpp"
#include "BulletTransformPayload.hpp"
#include "BulletSpawnTransform.hpp"
#include "BulletTransformCancel.hpp"
#include "BulletBoundaryBounce.hpp"
#include "BulletTransformsDay1.hpp"
#include "DirectionVector.hpp"
#include "BulletAppearanceTransform.hpp"
#include "BulletVelocityApproach.hpp"
#include "BulletTransformWait.hpp"

namespace th143 {
bool bullet_transform(BulletView b, BulletMotionHost& host, u32 global_rate_token) {
    for (;;) {
        const i32 cursor = signed_word(b.get(0xc20));
        if (cursor >= 18) return true;
        if (cursor < 0) return false;
        const u32 row = 0xc28 + u32(cursor) * 0x2c;
        const u32 type = b.get(row + 0x20), active = b.get(0xc04);
        if (!type || (!b.get(row + 0x24) && (active & 0xfffffeff)) || (type & active)) return true;
        switch (type) {
        case 0x80:start_bullet_lifetime_transform(b,row);continue;
        case 0x400000:start_bullet_scale_transform(b,row,global_rate_token);continue;
        case 0x1000000:if(!dispatch_bullet_enemy_transform(b,row,host))return false;continue;
        case 0x4000000:start_bullet_timed_freeze(b,row,global_rate_token);break;
        case 0x100:start_bullet_offscreen_grace(b,row,global_rate_token);break;
        case 0x800:if(!dispatch_bullet_sound_transform(b,row,host))return false;continue;
        case 0x4000:if(!consume_bullet_transform_payload(b))return false;continue;
        case 0x2000:if(!dispatch_bullet_spawn_transform(b,row,host))return false;continue;
        case 0x400:if(!dispatch_bullet_transform_cancel(b,row,host))return false;break;
        case 0x40:start_bullet_boundary_bounce(b,row);break;
        case 0x2000000:set_bullet_transform_wait(b,row);break;
        case 0x100000:b.put(0x40,b.get(row+0x10)?(b.get(0x40)&0xfffffe3fu)|0x20u:b.get(0x40)&0xfffffe1fu);break;
        case 0x200000:if(!start_bullet_velocity_approach_acceleration(b,row,host,global_rate_token))return false;break;
        case 0x200:if(!dispatch_bullet_appearance_transform(b,row,host))return false;break;
        case 16:if(!start_bullet_direction_change(b,row,host,global_rate_token))return false;break;
        case 4:if(!start_bullet_cartesian_acceleration(b,row,host,global_rate_token))return false;break;
        case 8:case 0x80000000:if(!start_bullet_extended_transform(b,row,type,host,global_rate_token))return false;break;
        case 1:
            b.put(0xc04, active | 1);
            if (!(b.get(0xf50) & 1)) {
                b.put(0xf4c, global_rate_token); b.put(0xf50, b.get(0xf50) | 1);
            }
            b.put(0xf40, 0xffffffff); b.put(0xf44, 0); b.put(0xf48, 0); b.put(0xf70, 0);
            break;
        case 2: {
            const i32 id = std::int16_t(b.get(row + 0x10) & 65535) + 7;
            if (!host.interrupt(b, 0, id)) return false;
            b.state(2);
            for (u32 i = 0; i < 3; ++i) {
                const float delta = b.floating(0xbcc + i * 4) * 4.f;
                b.put(0xbc0 + i * 4, word(b.floating(0xbc0 + i * 4) - delta));
            }
            break;
        }
        case 0x8000: b.put(0xbe8, b.get(row + 0x10)); break;
        default: return false;
        }
        b.put(0xc20, u32(cursor) + 1);
    }
}
i32 bullet_fast_velocity(BulletView b, BulletMotionHost& host) {
    if (signed_word(b.get(0xf44)) > 16) {
        b.put(0xc04, b.get(0xc04) ^ 1); return 1;
    }
    const float decay = (b.floating(0xf48) * 5.f) * .0625f;
    const float speed = (5.f - decay) + b.floating(0xbd8);
    DirectionVector vector;
    if (!direction_vector(b.floating(0xbdc), speed, vector)) return -2;
    b.put(0xbcc, word(vector.x)); b.put(0xbd0, word(vector.y));
    float rate = 1.f;
    const u32 token = b.get(0xf4c), previous = b.get(0xf44);
    if (token && !host.timer_rate(token, rate)) return -2;
    b.put(0xf40, previous);
    const bool scaled = token && !(rate > real(0x3f7d70a4) && rate < real(0x3f8147ae));
    const float fraction = b.floating(0xf48) + (scaled ? rate : 1.f);
    u32 current = previous + 1;
    if (scaled) current = !(fraction >= -2147483648.f && fraction < 2147483648.f) ? 0x80000000 : u32(i32(fraction));
    b.put(0xf44, current); b.put(0xf48, word(fraction));
    return 0;
}
}
