#include "BulletLifetimeTransform.hpp"
namespace th143 {void start_bullet_lifetime_transform(BulletView b,u32 row){const u32 value=b.get(row+0x10);b.put(0xc20,b.get(0xc20)+1);b.put(0x24,value);}}
