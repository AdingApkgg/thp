#include "BulletTransformWait.hpp"
namespace th143 {
void set_bullet_transform_wait(BulletView bullet, u32 row) {
    bullet.put(0xc24, bullet.get(row + 0x10));
}
}
