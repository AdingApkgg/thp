#include "../../cpp/game/EnemyState.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
API(player_aim) u32 player_aim(i32 id,float x,float y,float px,float py){
    EnemyState enemy{};EnemyEnvironment environment;
    enemy.current.position=enemy.absolute.position=enemy.relative.position={x,y,0};
    environment.player_position={px,py,0};
    EnemyGlobals globals(enemy,environment);return float_bits(float(globals.floating(id)));
}
