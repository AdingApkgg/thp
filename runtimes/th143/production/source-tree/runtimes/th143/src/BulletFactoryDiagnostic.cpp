#include "BulletFactory.hpp"
#include "BulletTransforms.hpp"
#include "DirectionVector.hpp"
#include <cmath>

namespace th143 {
namespace {u32 factory_failure[18]{};}
extern "C" __attribute__((export_name("campaign_bullet_factory_diagnostic"))) u32 campaign_bullet_factory_diagnostic(u32 i){return i<18?factory_failure[i]:0;}

namespace {
void reset_timer(BulletView b, u32 at, u32 rate) {
    if (!(b.get(at + 16) & 1)) { b.put(at + 12, rate); b.put(at + 16, b.get(at + 16) | 1); }
    b.put(at, 0xffffffff); b.put(at + 4, 0); b.put(at + 8, 0);
}
}
i32 bullet_create(BulletPool& pool, const u8* emitter, i32 inner, i32 outer, float aim,
                  Rng& rng, BulletFactoryHost& host, u32& token) {
    token = pool.acquire(); if (!token) return 1;
    BulletView b{pool.data.data() + BulletPool::offset(token)};
    const auto get = [&](u32 at) { u32 v; std::memcpy(&v, emitter + at, 4); return v; };
    const u32 type = get(0), color = get(4), definition = 0x4daf60 + type * 0x114;
    BulletDirection direction;
    auto fail=[&](u32 line)->i32{const u32 v[]={line,token,type,color,u32(inner),u32(outer),word(aim),word(direction.raw_angle),word(direction.speed),b.get(0xc04),b.get(0xc20),b.get(0x20),b.get(0x40),b.get(0xbd8),b.get(0xbdc),b.get(0xbc0),b.get(0xbc4),b.get(0x13ec)};std::memcpy(factory_failure,v,sizeof v);return -2;};

    if (!bullet_pattern(emitter, inner, outer, aim, rng, direction)) return fail(__LINE__);
    b.put(0xbd8, word(direction.speed)); b.put(0xbdc, word(direction.angle));
    for (u32 i = 0; i != 3; ++i) b.put(0xbc0 + i * 4, get(8 + i * 4));
    if (real(get(0x24)) != 0.f) {
        DirectionVector offset;
        if (!direction_vector(direction.angle, real(get(0x24)), offset)) return fail(__LINE__);
        b.put(0xbc0, word(b.floating(0xbc0) + offset.x)); b.put(0xbc4, word(offset.y + b.floating(0xbc4)));
    }
    b.put(0xbc8, 0x3dcccccd); b.put(0x20, b.get(0x20) | 1); b.state(1);
    reset_timer(b, 0x13c0, host.global_rate_token()); reset_timer(b, 0x13d4, host.global_rate_token());
    b.put(0x24, 0); b.put(0x13bc, word(1.f)); b.put(0x13b4, 0);
    const float forbidden = real(pool.get(0x60));
    if (forbidden > 0.f) {
        float x, y; if (!host.player_position(x, y)) return fail(__LINE__);
        x = b.floating(0xbc0) - x; y = b.floating(0xbc4) - y;
        const float distance = x * x + y * y;
        if (forbidden > distance) return pool.release(token, host.global_rate_token()) ? -1 : -2;
    }
    DirectionVector velocity;
    if (!direction_vector(direction.raw_angle, direction.speed, velocity)) return fail(__LINE__);
    b.put(0xbcc, word(velocity.x)); b.put(0xbd0, word(velocity.y));
    // 418440 writes two components; the old Z velocity remains intact.
    b.put(0xc04, get(0x36c)); b.put(0x13ec, (type & 65535) | (color << 16));
    b.put(0x20, (b.get(0x20) & ~12u) | 2); b.put(0xc18, 0);
    AnmView main{b.data + 0x28}, secondary{b.data + 0x5f4};
    anm_reset(main, token + 0x28); b.put(0x5d4, 0x417dc0); b.put(0x5d8, token);
    u32 script, secondary_script, layer, cancel, radius;
    if (!host.read(definition, &script, 4) || !host.read(definition + 0x110, &secondary_script, 4) ||
        !host.read(definition + 0x108, &layer, 4) || !host.read(definition + 0x10c, &cancel, 4) || !host.read(definition + 0x104, &radius, 4)) return fail(__LINE__);
    if (!anm_bind_script(main, pool.get(0x9bf6cc), signed_word(script), host)) return fail(__LINE__);
    b.put(0x20, b.get(0x20) | 0x10); b.put(0x44, (b.get(0x44) & ~0x40000u) | 0x20000);
    anm_reset(secondary, token + 0x5f4); b.put(0x60c, b.get(0x60c) & ~1u);
    if (secondary_script) {
        b.put(0x60c, b.get(0x60c) | 1);
        if (!anm_bind_script(secondary, pool.get(0x9bf6cc), signed_word(secondary_script), host)) return fail(__LINE__);
        b.put(0x610, (b.get(0x610) & ~0x40000u) | 0x20000);
    }
    b.put(0x13e8, definition);
    switch (cancel) {
    case 0: b.put(0xc00, color * 2 + 4); break;
    case 1: { u32 value; if (!host.read(0x4c4670 + color * 4, &value, 4)) return fail(__LINE__); b.put(0xc00, value); break; }
    case 2: b.put(0xc00, 0xffffffff); b.put(0x20, b.get(0x20) | 0x10); break;
    case 3: b.put(0xc00, 16); break;
    case 4: b.put(0xc00, 6); break;
    case 6: { u32 value; if (!host.read(definition + 0x10 + color * 16, &value, 4)) return fail(__LINE__);
        b.put(0xc00, value); b.put(0x20, b.get(0x20) | 0x10); break; }
    case 7: case 8: case 9: case 10:
        b.put(0xc00, cancel == 7 ? 0xe8 : cancel == 8 ? 0xeb : cancel == 9 ? 0xee : 0xf7);
        b.put(0x20, b.get(0x20) | 0x10); break;
    default: break;
    }
    b.put(0xc24, layer); b.put(0xc1c, get(0x374)); b.put(0xbfc, 5); b.put(0xbe0, radius); b.put(0xbe4, radius);
    b.put(0xc08, get(0x36c)); b.put(0xc04, 0); b.put(0xc20, get(0x378));
    std::memcpy(b.data + 0xc28, emitter + 0x28, 0x318);
    const i32 cursor = signed_word(b.get(0xc20));
    if (cursor < 0 || cursor > 18) return fail(__LINE__);
    if (get(0x48 + u32(cursor) * 0x2c) == 2) {
        const i32 subtype = std::int16_t(get(0x38 + u32(cursor) * 0x2c) & 65535);
        if (subtype != 1 && !host.interrupt(b, 0, subtype + 7)) return fail(__LINE__);
        b.state(2);
        for (u32 i = 0; i != 3; ++i) b.put(0xbc0 + i * 4, word(b.floating(0xbc0 + i * 4) - b.floating(0xbcc + i * 4) * 4.f));
        b.put(0xc20, u32(cursor) + 1);
    } else if (!host.interrupt(b, 0, 2)) return fail(__LINE__);
    if (!bullet_transform(b, host, host.global_rate_token())) return fail(__LINE__);
    if (host.animate(b, 0) == -2) return fail(__LINE__);
    if ((b.get(0x60c) & 1) && host.animate(b, 1) == -2) return fail(__LINE__);
    return 0;
}
bool bullet_launch(BulletPool& pool, const u8* emitter, Rng& rng, BulletFactoryHost& host, BulletLaunchResult& result) {
    const auto get = [&](u32 at) { u32 v; std::memcpy(&v, emitter+at, 4); return v; };
    float x, y; if (!host.aim_position(x, y)) return false;
    x -= real(get(8)); y -= real(get(12));
    result = {};
    result.aim = x == 0.f && y == 0.f ? real(0x3fc90fdb) : float(std::atan2(double(y), double(x)));
    if (!std::isfinite(result.aim)) return false;
    const i32 inner_count = std::int16_t(get(0x364) & 65535), outer_count = std::int16_t(get(0x364) >> 16);
    for (i32 outer = 0; outer < outer_count && !result.exhausted; ++outer) {
        for (i32 inner = 0; inner < inner_count; ++inner) {
            u32 token; ++result.attempts;
            const i32 status = bullet_create(pool, emitter, inner, outer, result.aim, rng, host, token);
            if (status == -2) return false;
            if (status == 1) { result.exhausted = true; break; }
            if (status == -1) ++result.rejected;
            else ++result.created;
        }
    }
    return !(get(0x36c) & 0x20) || host.launch_sound(signed_word(get(0x370)), real(get(8)));
}
}
