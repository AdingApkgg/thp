#include "../../cpp/game/BulletState.hpp"
#include "../../cpp/game/BulletTh14.hpp"
#include "../../cpp/game/EclContext.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static BulletEnvironment world;static BulletState bullet;
API(begin) i32 begin(i32 mode,i32 duration,float rate,float start,float target){
 bullet={};world.rate=rate;bullet.flags=0x12;bullet.th14_size_current=.625f;bullet.th14_size=1;
 auto& t=bullet.th14_transforms[0];t.a=start;t.b=target;t.p=duration;t.q=mode;t.opcode=0x400000;return bullet_th14_start_transforms(bullet,world);
}
API(tick) void tick(){bullet_th14_size_tick(bullet,world);}
API(word) u32 word(u32 n){const auto& b=bullet;const auto& s=b.th14_size_interpolation;const u32 v[]={b.active_transforms,u32(b.transform_index),b.flags,float_bits(s.start[0]),float_bits(s.end[0]),float_bits(s.initial_tangent[0]),float_bits(s.final_tangent[0]),float_bits(b.th14_size_current),u32(s.timer.previous),u32(s.timer.current),float_bits(s.timer.fractional),u32(s.duration),u32(s.mode),float_bits(b.th14_size)};return v[n];}
