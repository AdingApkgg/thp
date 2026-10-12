#include "../../cpp/game/BulletState.hpp"
#include "../../cpp/game/BulletTh14.hpp"
#include "../../cpp/game/EclContext.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static BulletEnvironment world;static BulletState bullet;static AnmSprite sprite;
API(initialize) i32 initialize(float x,float y,float angle,float sw,float sh,i32 count,i32 early,float rate){bullet={};world.rate=rate;bullet.position={x,y,3.25f};bullet.angle=angle;sprite.width=sw;sprite.height=sh;bullet.vm.sprite=&sprite;auto& t=bullet.th14_transforms[0];t.opcode=0x100;t.p=count;t.q=early;return bullet_th14_start_transforms(bullet,world);}
API(tick) i32 tick(){return bullet_th14_offscreen_hold_tick(bullet,world);}
API(value) u32 value(u32 n){const auto& s=bullet.motion[6];const u32 v[]={bullet.active_transforms,u32(bullet.transform_index),u32(s.timer.previous),u32(s.timer.current),float_bits(s.timer.fractional),u32(s.duration)};return v[n];}
