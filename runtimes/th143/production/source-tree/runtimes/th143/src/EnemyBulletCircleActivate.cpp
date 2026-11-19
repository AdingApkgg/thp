#include "EnemyBulletCircleActivate.hpp"
#include "DirectionVector.hpp"
namespace th143 {
bool enemy_bullet_circle_activate(AnmView actor, BulletPool& pool, const std::function<bool(i32)>& sound, i32& result) {
    const float radius_squared = actor.floating(0x33c) * actor.floating(0x33c);
    const float x = actor.floating(0x340), y = actor.floating(0x344);
    u32 node = pool.get(0x80), visited = 0;
    pool.put(0x9bf6c0, node);
    pool.put(0x9bf6c4, node ? pool.get(BulletPool::offset(node) + 4) : 0);
    while (node) {
        if (++visited > BulletPool::count) return false;
        const u32 pointer = pool.get(BulletPool::offset(node));
        if (pointer < BulletPool::bullet(0) || pointer > BulletPool::bullet(BulletPool::count - 1)) return false;
        AnmView bullet{pool.data.data() + BulletPool::offset(pointer)};
        const float dx = x - bullet.floating(0xbc0), dy = y - bullet.floating(0xbc4);
        if (!bullet.get(0xc18) && radius_squared >= dx * dx + dy * dy) {
            bullet.put(0xc20, 8);
            bullet.put(0xc04, 0);
            bullet.put(0xc18, 1);
            DirectionVector velocity;
            if (!direction_vector(bullet.floating(0xbdc), bullet.floating(0xbd8), velocity)) return false;
            bullet.put(0xbcc, word(velocity.x));
            bullet.put(0xbd0, word(velocity.y));
            if (signed_word(bullet.get(0xc1c)) >= 0 && !sound(signed_word(bullet.get(0xc1c)))) return false;
        }
        node = pool.get(0x9bf6c4);
        pool.put(0x9bf6c0, node);
        pool.put(0x9bf6c4, node ? pool.get(BulletPool::offset(node) + 4) : 0);
    }
    result = 0;
    return true;
}
}
