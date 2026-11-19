#include "EnemyRandomInteger.hpp"
namespace th143 {
bool enemy_random_integer(Rng& random,i32 id,i32& value){
 if(id!=-10000)return false;
 value=i32(random.next32()&0x7fffffffu);return true;
}
}
