#include "BulletPool.hpp"
#include <algorithm>

namespace th143 {
u32 BulletPool::get(u32 at) const { u32 v; std::memcpy(&v, data.data() + at, 4); return v; }
void BulletPool::put(u32 at, u32 v) { std::memcpy(data.data() + at, &v, 4); }
void BulletPool::build_free_list() {
    put(0x10, bullet(0));
    const std::uint16_t sentinel_state = 6;
    std::memcpy(data.data() + first + count * stride + 0xc0e, &sentinel_state, 2);
    for (u32 off : {0x6cu, 0x70u, 0x74u, 0x78u}) put(off, 0);
    for (u32 i = 0; i < count; ++i) {
        const u32 b = first + i * stride;
        for (u32 off = 0; off < 32; off += 4) put(b + off, 0);
        put(b + 0x10, token(b));
        const u32 next = get(0x70);
        if (next) {
            put(b + 4, next);
            put(offset(next) + 8, token(b));
        }
        if (get(0x78)) put(0x78, token(b));
        put(0x70, token(b)); put(b + 8, token(0x6c));
    }
    for (u32 off : {0x7cu, 0x80u, 0x84u, 0x88u}) put(off, 0);
}
void BulletPool::initialize(u32 resource, u32 update, u32 draw) {
    std::fill(data.begin(), data.end(), 0);
    put(8, update); put(0xc, draw); put(0x9bf6cc, resource);
    build_free_list();
}
u32 BulletPool::acquire() {
    const u32 address = get(0x70);
    if (!address) return 0;
    const u32 b = offset(address), next = get(b + 4), previous = get(b + 8);
    if (next) put(offset(next) + 8, previous);
    if (previous) put(offset(previous) + 4, next);
    put(b + 4, 0); put(b + 8, 0);
    const u32 live = token(b + 0x10), head = get(0x80);
    if (head) {
        put(b + 0x14, head);
        put(offset(head) + 8, live);
    }
    if (get(0x88)) put(0x88, live);
    put(0x80, live); put(b + 0x18, token(0x7c));
    return address;
}
void BulletPool::reset_timer(u32 at, u32 rate) {
    if (!(get(at + 16) & 1)) {
        put(at + 12, rate); put(at + 16, get(at + 16) | 1);
    }
    put(at, 0xffffffff); put(at + 4, 0); put(at + 8, 0);
}
bool BulletPool::release(u32 address, u32 rate) {
    if (address < bullet(0) || address >= bullet(count) || (address - bullet(0)) % stride) return false;
    const u32 b = offset(address);
    if (!(get(b + 0xc0c) >> 16)) return true;
    put(b + 0xc0c, get(b + 0xc0c) & 0xffff);
    reset_timer(b + 0x13c0, rate); reset_timer(b + 0x13d4, rate);
    put(b + 0x20, get(b + 0x20) & 0xfffffcbe);
    put(b + 0xc18, 0); put(b + 0xbe8, 0);
    const u32 free_head = get(0x70);
    if (free_head) {
        put(b + 4, free_head); put(offset(free_head) + 8, address);
    }
    if (get(0x78)) put(0x78, address);
    put(0x70, address); put(b + 8, token(0x6c));
    const u32 next = get(b + 0x14), previous = get(b + 0x18);
    if (next) put(offset(next) + 8, previous);
    if (previous) put(offset(previous) + 4, next);
    put(b + 0x14, 0); put(b + 0x18, 0);
    return true;
}
void BulletPool::reset_storage() {
    std::fill(data.begin() + first, data.begin() + 0x9bf6c0, 0);
    build_free_list();
    put(0x64, 0); put(0x68, 0); put(0x9bf6c8, 0);
}
}
