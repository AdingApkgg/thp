#include "BulletManager.hpp"

namespace th143 {
namespace {
bool valid(u32 token, u32 size) {
    return token >= BulletPool::token_base &&
        std::uint64_t(token) + size <= std::uint64_t(BulletPool::token_base) + BulletPool::bytes;
}
u32 truncate(float v) { return v >= -2147483648.f && v < 2147483648.f ? u32(i32(v)) : 0x80000000; }
bool age(BulletView b, BulletManagerHost& host) {
    float rate = 1.f;
    const u32 pointer = b.get(0x13cc), current = b.get(0x13c4);
    if (pointer && !host.timer_rate(pointer, rate)) return false;
    b.put(0x13c0, current);
    if (pointer && !(rate > real(0x3f7d70a4) && rate < real(0x3f8147ae))) {
        const float fraction = b.floating(0x13c8) + rate;
        b.put(0x13c4, truncate(fraction)); b.put(0x13c8, word(fraction));
    } else {
        b.put(0x13c4, current + 1); b.put(0x13c8, word(b.floating(0x13c8) + 1.f));
    }
    return true;
}
}
bool bullet_manager_step(BulletPool& pool, u32 root_flags, BulletManagerHost& host) {
    u32 node = pool.get(0x80);
    auto prefetch = [&]() -> bool {
        if (node && !valid(node, 8)) return false;
        pool.put(0x9bf6c0, node);
        pool.put(0x9bf6c4, node ? pool.get(BulletPool::offset(node) + 4) : 0);
        return true;
    };
    if (!prefetch()) return false;
    pool.put(0x5c, 0);
    for (u32 at = 0x14; at <= 0x40; at += 4) pool.put(at, 0);
    for (u32 iteration = 0; node; ++iteration) {
        if (iteration >= BulletPool::count) return false;
        const u32 token = pool.get(BulletPool::offset(node));
        if (!valid(token, BulletPool::stride)) return false;
        BulletView bullet{pool.data.data() + BulletPool::offset(token)};
        i32 status = 0;
        if (!(root_flags & 0x400)) {
            const u32 state = bullet.state();
            if ((bullet.get(0x20) & 0x100) && (state == 1 || (state == 2 && signed_word(bullet.get(0x13c4)) >= 8))) {
                if (!host.forced_contact(bullet, token)) return false;
            } else if (!host.update(bullet, token, status)) return false;
        }
        if (!status) {
            if (!(bullet.get(0x20) & 0x200)) {
                const u32 layer = bullet.get(0xc24);
                if (layer >= 6) return false;
                if (pool.get(0x14 + layer * 4)) {
                    const u32 tail = pool.get(0x2c + layer * 4);
                    if (!valid(tail, BulletPool::stride)) return false;
                    pool.put(BulletPool::offset(tail) + 0xc14, token);
                } else pool.put(0x14 + layer * 4, token);
                pool.put(0x2c + layer * 4, token); bullet.put(0xc14, 0);
            }
            pool.put(0x5c, pool.get(0x5c) + 1);
            if (!age(bullet, host)) return false;
        }
        node = pool.get(0x9bf6c4);
        if (!prefetch()) return false;
    }
    return true;
}
}
