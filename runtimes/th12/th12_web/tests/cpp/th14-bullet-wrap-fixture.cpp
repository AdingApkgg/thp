#include "../../cpp/game/BulletState.hpp"
#include "../../cpp/game/BulletTh14.hpp"
#include "../../cpp/game/EclContext.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
namespace {
struct World:BulletEnvironment{u32 sounds=0;bool sound(i32,float,bool)override{++sounds;return true;}} world;
BulletState bullet;AnmSprite sprite;
}
API(initialize) i32 initialize(i32 flags,i32 limit,float x,float y,float sw,float sh,i32 sound){bullet={};world.sounds=0;bullet.position={x,y,3.25f};sprite.width=sw;sprite.height=sh;bullet.vm.sprite=&sprite;bullet.transform_sound=sound;auto& t=bullet.th14_transforms[0];t.opcode=0x1000;t.p=limit;t.q=flags;return bullet_th14_start_transforms(bullet,world);}
API(tick) i32 tick(){return bullet_th14_wrap_tick(bullet,world);}
API(value) u32 value(u32 n){const auto& b=bullet;const auto& s=b.motion[5];const u32 values[]={b.active_transforms,u32(b.transform_index),float_bits(b.position.x),float_bits(b.position.y),float_bits(b.position.z),u32(s.count),u32(s.limit),u32(s.duration),world.sounds};return values[n];}
static u32 blend_flags,blend_extra;
API(blend) i32 blend(u32 flags,i32 p,u32 active,u32 concurrent){bullet={};bullet.vm.flags=(0xa55a5aa5u&~0x70u)|((flags>>1)&0x70u);bullet.vm.th13_native_flags=(0x5aa5a55au&~0x100u)|(flags&0x100u);blend_flags=bullet.vm.flags;blend_extra=bullet.vm.th13_native_flags;bullet.active_transforms=active;auto& t=bullet.th14_transforms[0];t.opcode=0x100000;t.p=p;t.concurrent=i32(concurrent);return bullet_th14_start_transforms(bullet,world);}
API(blend_value) u32 blend_value(u32 n){const u32 v[]={u32(bullet.transform_index),bullet.active_transforms,bullet.vm.blend_mode(),u32((bullet.vm.flags&~0x70u)==(blend_flags&~0x70u)&&(bullet.vm.th13_native_flags&~0x100u)==(blend_extra&~0x100u))};return v[n];}
