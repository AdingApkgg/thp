#include "../../cpp/game/ShotManager.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static ShotState shot;static Th14DamageArea area;static Rng visual;
API(spawn) void spawn(u32 seed,float angle,u32 flags){shot={};visual.seed=u16(seed);visual.calls=123;shot.movement.angle=angle;shot.th14_shot_flags=flags;shot_th14_flame_spawn(shot,visual);}
API(spawn_value) u32 spawn_value(u32 n){const u32 v[]={float_bits(shot.movement.angle),shot.th14_shot_flags,visual.seed,visual.calls};return v[n];}
API(update) i32 update(u32 seed,float speed,i32 age,u32 flags,i32 damage,i32 present){shot={};area={};visual.seed=u16(seed);visual.calls=123;shot.movement.speed=speed;shot.timer.current=age;shot.th14_shot_flags=flags;area.damage=damage;return shot_th14_flame_update(shot,present?&area:nullptr,visual);}
API(value) u32 value(u32 n){const u32 v[]={float_bits(shot.movement.speed),shot.th14_shot_flags,u32(area.damage),visual.seed,visual.calls};return v[n];}
API(small) i32 small(i32 state,float speed,i32 age,i32 advanced){shot={};shot.state=state;shot.movement.speed=speed;shot.timer.current=age;shot.timer.previous=age-advanced;return shot_th14_small_flame_update(shot);}
API(small_value) u32 small_value(u32 n){return n?u32(shot.state):float_bits(shot.movement.speed);}
