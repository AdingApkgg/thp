#include "BulletScaleTransform.hpp"
#include "BulletTimedFreeze.hpp"
#include "BulletOffscreenGrace.hpp"
#include "BulletBoundaryBounceRuntime.hpp"
#include "BulletMotionDay1.hpp"
#include "BulletTransforms.hpp"
#include <climits>
#include "BulletVelocityApproach.hpp"

namespace th143 {
namespace {
u32 truncate(float value) {
    if (!(value >= -2147483648.f && value < 2147483648.f)) return 0x80000000;
    return u32(i32(value));
}
bool advance_timer(BulletView b, u32 at, BulletMotionHost& host) {
    float rate = 1.f;
    const u32 token = b.get(at + 12);
    if (token && !host.timer_rate(token, rate)) return false;
    const u32 previous = b.get(at + 4);
    b.put(at, previous);
    if (token && !(rate > real(0x3f7d70a4) && rate < real(0x3f8147ae))) {
        const float fraction = b.floating(at + 8) + rate;
        b.put(at + 4, truncate(fraction)); b.put(at + 8, word(fraction));
    } else {
        b.put(at + 4, previous + 1); b.put(at + 8, word(b.floating(at + 8) + 1.f));
    }
    return true;
}
void move(BulletView b, float elapsed, bool half) {
    for (u32 i = 0; i < 3; ++i) {
        float delta = b.floating(0xbcc + i * 4) * elapsed;
        if (half) delta *= .5f;
        b.put(0xbc0 + i * 4, word(b.floating(0xbc0 + i * 4) + delta));
    }
}
}
namespace { u32 day1_failure[16]{}; }
extern "C" __attribute__((export_name("day1_bullet_failure"))) u32 day1_bullet_failure(u32 i){return i<16?day1_failure[i]:0;}
i32 bullet_step(BulletView b, float elapsed, BulletMotionHost& host) {
    auto fail=[&](u32 line)->i32{day1_failure[0]=line;u32 at[]={0xc04,0xc20,0x20,0x40,0x54,0x60c,0x13ec,0x13c4,0x4d4,0xbc0,0xbc4,0xbcc,0xbd0};for(u32 i=0;i<13;++i)day1_failure[i+1]=b.get(at[i]);day1_failure[14]=b.state();const i32 cursor=signed_word(b.get(0xc20));day1_failure[15]=cursor>=0&&cursor<18?b.get(0xc28+u32(cursor)*0x2c+0x20):0;return -2;};

    if (!advance_timer(b, 0x13d4, host)) return fail(__LINE__);
    auto retire = [&]() -> i32 { host.retire(b); return -1; };
    if (b.get(0x20) & 8) return retire();
    struct ScaleRates:AnmTimerHost{BulletMotionHost& h;explicit ScaleRates(BulletMotionHost& p):h(p){}bool timer_rate(u32 p,float& v)override{return h.timer_rate(p,v);}u32 global_rate_token()const override{return 0x4e40b0;}}scale_rates{host};
    if(!update_bullet_scale_transform(b,scale_rates))return fail(__LINE__);
    bool ordinary = b.state() == 1;
    switch (b.state()) {
    case 2: {
        move(b, elapsed, true);
        bool collided = false;
        if (signed_word(b.get(0x13c4)) >= 8) {
            const i32 result = host.collision(b, false);
            if (result == -2) return fail(__LINE__);
            collided = result == 1;
        }
        if (!collided && b.get(0x4d4)) { b.state(1); ordinary = true; }
        break;
    }
    case 3: move(b, elapsed, true); break;
    case 5: {
        const i32 age = signed_word(b.get(0x13c4));
        if (age >= 3) {
            if (age == 3 && !host.cancellation_effect(b)) return fail(__LINE__);
            move(b, elapsed, true);
        }
        break;
    }
    }
    if (ordinary) {
        for (u32 iteration = 0;; ++iteration) {
            if (iteration >= 64) return fail(__LINE__);
            if (!(b.get(0xc04) & 0x4000000) && !bullet_transform(b, host, 0x4e40b0)) return fail(__LINE__);
            bool changed = false;
            if (b.get(0xc04)) {
                if(b.get(0xc04)&~0x8460015du)return fail(__LINE__);
                i32 total=0,result=0;if(b.get(0xc04)&1){result=bullet_fast_velocity(b,host);if(result==-2)return fail(__LINE__);total+=result;}
                if(b.get(0xc04)&4){result=bullet_cartesian_acceleration(b,host);if(result==-2)return fail(__LINE__);total+=result;}
                if(b.get(0xc04)&8){result=bullet_polar_acceleration(b,host);if(result==-2)return fail(__LINE__);total+=result;}
                if(b.get(0xc04)&0x200000){result=bullet_velocity_approach_acceleration(b,host);if(result==-2)return fail(__LINE__);total+=result;}
                if(b.get(0xc04)&16){result=bullet_direction_change(b,host);if(result==-2)return fail(__LINE__);total+=result;}
                if(b.get(0xc04)&0x40){result=dispatch_bullet_boundary_bounce(b,host);if(result==-2)return fail(__LINE__);total+=result;}
                if(b.get(0xc04)&0x100){result=update_bullet_offscreen_grace(b,host);if(result==-2)return fail(__LINE__);total+=result;}
                if(b.get(0xc04)&0x80000000){result=bullet_transform_wait(b,host);if(result==-2)return fail(__LINE__);total+=result;}
                if(b.get(0xc04)&0x4000000){result=update_bullet_timed_freeze(b,host);if(result==-2)return fail(__LINE__);total+=result;}
                changed=total!=0;
                if (b.get(0x24)) b.put(0x24, b.get(0x24) - 1);
            }
            if (!changed) break;
        }
        if (!(b.get(0x20) & 0x200)) {
            move(b, elapsed, false);
            if (host.collision(b, false) == -2) return fail(__LINE__);
        }
    }
    if (b.get(0x54) && (b.get(0xc04) & 0x1000)) return fail(__LINE__);
    if (b.get(0x54) && !(b.get(0xc04) & 0x100) && signed_word(b.get(0xbfc)) < 1) {
        float width, height;
        if (!host.sprite_dimensions(b.get(0x54), width, height)) return fail(__LINE__);
        const float half_width = width * b.floating(0x13bc) * .5f;
        const float half_height = height * b.floating(0x13bc) * .5f;
        const float x = b.floating(0xbc0), y = b.floating(0xbc4);
        if (-192.f >= x + half_width || x - half_width >= 192.f ||
            -64.f >= y + half_height || y - half_height >= 448.f) return retire();
    }
    if (b.get(0x24)) b.put(0x24, b.get(0x24) - 1);
    if (signed_word(b.get(0xbfc)) > 0) b.put(0xbfc, b.get(0xbfc) - 1);
    if (!(b.get(0x20) & 0x200)) {
        const i32 status = host.animate(b, 0);
        if (status == -2) return fail(__LINE__);
        if (status) return retire();
    }
    if (b.get(0x60c) & 1) {
        if (host.animate(b, 1) == -2) return fail(__LINE__);
    }
    return 0;
}
}
