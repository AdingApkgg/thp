#include "EnemyScriptFloatCells.hpp"
namespace th143 {
u8* enemy_script_float_reference(AnmView actor,i32 id){
 if(!actor.data)return nullptr;
 if(id>=-9981&&id<=-9978)return actor.data+0x33c+u32(id+9981)*4;
 if(id>=-9935&&id<=-9932)return actor.data+0x34c+u32(id+9935)*4;
 return nullptr;
}
bool enemy_script_float_value(AnmView actor,i32 id,float& value){
 auto* cell=enemy_script_float_reference(actor,id);if(!cell)return false;std::memcpy(&value,cell,4);return true;
}
}
