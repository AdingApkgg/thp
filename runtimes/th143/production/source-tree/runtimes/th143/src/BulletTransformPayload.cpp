#include "BulletTransformPayload.hpp"
namespace th143 {
bool consume_bullet_transform_payload(BulletView bullet){
 const i32 cursor=signed_word(bullet.get(0xc20));
 if(cursor<0||cursor>=18||bullet.get(0xc28+u32(cursor)*0x2c+0x20)!=0x4000)return false;
 bullet.put(0xc20,u32(cursor)+1);return true;
}
}
