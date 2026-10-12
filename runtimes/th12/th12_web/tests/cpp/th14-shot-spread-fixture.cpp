#include "../../cpp/game/ShotManager.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static ShotState shot;static Rng visual,script;static float rate;
API(spawn) void spawn(u32 seed,float angle,u32 flags){shot={};visual.seed=u16(seed);visual.calls=123;script.seed=54321;script.calls=77;shot.movement.angle=angle;shot.th14_shot_flags=flags;shot_th14_spread_spawn(shot,visual);}
API(spawn_value) u32 spawn_value(u32 n){const u32 v[]={float_bits(shot.movement.angle),shot.th14_shot_flags,visual.seed,visual.calls,script.seed,script.calls};return v[n];}
API(update) void update(i32 state,float speed,i32 advanced,float r){shot={};rate=r;shot.state=state;shot.movement.speed=speed;shot.timer.set(17,&rate);shot.timer.previous=17-advanced;shot_th14_accelerating_update(shot);}
API(update_value) u32 update_value(u32 n){return n?float_bits(shot.movement.speed):u32(shot.state);}
