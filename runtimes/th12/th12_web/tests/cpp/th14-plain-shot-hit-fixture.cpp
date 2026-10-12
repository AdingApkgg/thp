#include "../../cpp/game/ShotManager.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static ShotSpec spec;static ShotState shot;static ShotPlayer player;static Rng rng;static Th14PlainHit result;
API(run) i32 run(u32 callback,i32 power,i32 age,u32 focus,u32 seed,float angle){spec={};spec.extra_callback=callback;spec.native_tail[0]=17;shot={};shot.spec=&spec;shot.timer.current=age;shot.th14_was_focused=focus;shot.movement.angle=angle;shot.movement.position={12.25,301,.1};player={};player.power_step=40;player.power=power*40;player.th14_plain_hits=1234;player.th14_focused_hits=5678;rng.seed=u16(seed);rng.calls=123;return shot_th14_plain_hit(shot,player,rng,result);}
API(count) u32 count(){return result.effect?10:5;}
API(value) u32 value(u32 n){const u32 a[]={player.th14_plain_hits,player.th14_focused_hits,rng.seed,rng.calls,150,float_bits(result.position.x),float_bits(result.position.y),float_bits(result.position.z),float_bits(result.angle),result.color};if(!result.effect&&n==4)return 0;return a[n];}
