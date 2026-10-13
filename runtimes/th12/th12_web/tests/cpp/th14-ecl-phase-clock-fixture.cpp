#include "../../cpp/game/EnemyState.hpp"
using namespace th11;
static EnemyState enemy{};
static EnemyEnvironment environment{};
static EnemyGlobals globals(enemy,environment);
#define API(name) extern "C" __attribute__((export_name(#name)))
API(set_clocks) void set_clocks(i32 phase,u32 fractional,i32 lifetime,u32 lifetime_fractional){
    enemy.timer_2bc.current=phase;enemy.timer_2bc.fractional=float_bits(fractional);
    enemy.lifetime.current=lifetime;enemy.lifetime.fractional=float_bits(lifetime_fractional);
}
API(read_integer) u32 read_integer(){return u32(globals.integer(-9988));}
API(read_float) u32 read_float(){return float_bits(float(globals.floating(-9988)));}
