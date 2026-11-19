#include "EnemyHealthVariable.hpp"
namespace th143 {
bool enemy_health_variable(AnmView actor,i32 id,i32& value){if(id!=-9954)return false;value=signed_word(actor.get(0x4018));return true;}
}
