#include "../../cpp/game/ShotManager.hpp"
#include "../../cpp/game/EclContext.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
namespace {ShotState s;ShotPlayer p;Rng rng;Th14FocusedHit hit;float rate=1;}
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(run) u32 run(const u32* args){
    s={};p={};rng={u16(args[3]),0,123};s.timer.set(i32(args[0]),&rate);s.timer.previous=i32(args[0])-i32(args[1]);s.movement.position={17,123,.1f};s.movement.speed=8;s.movement.angle=float_bits(args[5]);s.th14_saved_speed=float_bits(args[6]);s.th14_decay.set(10,&rate);s.th14_area_radius=float_bits(args[4]);s.damage=19;p.power=i32(args[2])*40;p.power_step=40;p.th14_focused_hits=1234;
    return shot_th14_focused_hit(s,p,rng,&rate,hit);
}
API(value) u32 value(u32 n){const u32 values[]={float_bits(s.movement.speed),float_bits(s.th14_saved_speed),u32(s.th14_decay.previous),u32(s.th14_decay.current),float_bits(s.th14_decay.fractional),p.th14_focused_hits,rng.seed,rng.calls,u32(hit.active),u32(hit.damage),float_bits(hit.position.x),float_bits(hit.position.y),float_bits(hit.position.z),float_bits(hit.angle)};return values[n];}
