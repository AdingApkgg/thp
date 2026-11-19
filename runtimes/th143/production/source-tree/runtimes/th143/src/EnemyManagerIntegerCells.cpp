#include "EnemyManagerIntegerCells.hpp"
namespace th143 {
u8* enemy_manager_integer_reference(AnmView manager,i32 id){
 if(!manager.data)return nullptr;
 if(id>=-9949&&id<=-9947)return manager.data+0x10+u32(id+9949)*4;
 if(id>=-9926&&id<=-9923)return manager.data+0x2c+u32(id+9926)*4;
 return nullptr;
}
bool enemy_manager_integer_value(AnmView manager,i32 id,i32& value){
 const auto* pointer=enemy_manager_integer_reference(manager,id);if(!pointer)return false;
 std::memcpy(&value,pointer,4);return true;
}
}
