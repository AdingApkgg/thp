#include "EnemyBossPositionVariables.hpp"
namespace th143 {
bool enemy_boss_position_variable(AnmView boss,i32 id,float& value){
 if(id!=-9963&&id!=-9962)return false;value=boss.data?boss.floating(id==-9963?0x44:0x48):id==-9963?0.f:128.f;return true;
}
}
