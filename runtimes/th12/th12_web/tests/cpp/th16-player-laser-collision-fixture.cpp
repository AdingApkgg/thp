#include "../../cpp/game/PlayerCollision.hpp"
#include "../../cpp/game/EclContext.hpp"
#include <cstdlib>
using namespace th11;
static PlayerCollisionResult result;
extern "C" {
__attribute__((export_name("allocate"))) void* allocate(u32 n){return std::malloc(n);}
__attribute__((export_name("release"))) void release(void* p){std::free(p);}
__attribute__((export_name("run"))) u32 run(const u32* p){
    PlayerCollision player;player.position={float_bits(p[0]),float_bits(p[1])};player.state=i32(p[9]);player.invincibility_frames=i32(p[10]);player.dialogue_active=p[11]!=0;
    result=player.laser({float_bits(p[2]),float_bits(p[3])},{float_bits(p[4]),float_bits(p[5])},float_bits(p[6]),float_bits(p[7]),float_bits(p[8]),p[12]!=0);return u32(result.kind);
}
__attribute__((export_name("trigger"))) u32 trigger(){return result.trigger_hit;}
}
