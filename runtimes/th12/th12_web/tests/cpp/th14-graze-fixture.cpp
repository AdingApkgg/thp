#include "../../cpp/game/GameEconomy.hpp"
#include "../../cpp/game/EclContext.hpp"
#include <cstdlib>
using namespace th11;
static GameEconomy economy;static Vec3 effect;
extern "C" {
__attribute__((export_name("allocate"))) void* allocate(u32 n){return std::malloc(n);}
__attribute__((export_name("release"))) void release(void* p){std::free(p);}
__attribute__((export_name("run"))) void run(const u32* p){economy.graze=i32(p[0]);economy.point_value=i32(p[1]);economy.max_point_value=i32(p[2]);effect=th14_graze(economy,{float_bits(p[3]),float_bits(p[4]),float_bits(p[5])},{float_bits(p[6]),float_bits(p[7]),float_bits(p[8])});}
__attribute__((export_name("value"))) u32 value(u32 n){switch(n){case 0:return u32(economy.graze);case 1:return u32(economy.point_value);case 2:return 24;case 3:return float_bits(effect.x);case 4:return float_bits(effect.y);case 5:return float_bits(effect.z);case 6:return 42;default:return 0;}}
}
