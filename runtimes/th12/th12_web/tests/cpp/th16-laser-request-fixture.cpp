#include "../../cpp/game/EnemyCommands.hpp"
#include <cstdlib>
using namespace th11;
#define EXPORT extern "C" __attribute__((visibility("default")))
EXPORT void* allocate(u32 size){return std::malloc(size);}
EXPORT void release(void* p){std::free(p);}
EXPORT i32 request(const u8* initial,u32 index,const u32* position,u8* out){EnemyState enemy;std::memcpy(&enemy.th16_emitters,initial,sizeof enemy.th16_emitters);enemy.current.position={float_bits(position[0]),float_bits(position[1]),float_bits(position[2])};return enemy_th16_laser_request(enemy,index,out)&&std::memcmp(&enemy.th16_emitters,initial,sizeof enemy.th16_emitters)==0;}
