#include "EnemyAimVariables.hpp"
namespace th143 {
bool enemy_aim_variable(EnemyScriptServices& services,i32 id,float& value){
    if(id!=-9965&&id!=-9964)return false;
    float x,y;if(!services.aim_position(x,y))return false;
    value=id==-9965?x:y;return true;
}
}
