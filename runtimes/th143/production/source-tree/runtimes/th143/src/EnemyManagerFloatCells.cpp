#include "EnemyManagerFloatCells.hpp"
namespace th143 {
u8* enemy_manager_float_reference(AnmView manager,i32 id){if(!manager.data||id<-9922||id>-9915)return nullptr;return manager.data+0x3c+u32(id+9922)*4;}
bool enemy_manager_float_value(AnmView manager,i32 id,float& value){auto* p=enemy_manager_float_reference(manager,id);if(!p)return false;std::memcpy(&value,p,4);return true;}
}
