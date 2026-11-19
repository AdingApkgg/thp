#include "EnemyBossIntegerVariables.hpp"
namespace th143 {
bool enemy_boss_integer_variable(AnmView boss,i32 id,i32& value){if(id<-9943||id>-9940)return false;value=boss.data?signed_word(boss.get(0x32c+u32(id+9943)*4)):0;return true;}
}
