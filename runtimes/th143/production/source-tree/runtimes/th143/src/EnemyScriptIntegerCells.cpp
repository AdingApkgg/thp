#include "EnemyScriptIntegerCells.hpp"
namespace th143 {
u8* enemy_script_integer_reference(AnmView actor,i32 id){
    if(!actor.data||id < -9985||id > -9982)return nullptr;
    return actor.data+0x32c+u32(id+9985)*4;
}
bool enemy_script_integer_value(AnmView actor,i32 id,i32& value){
    auto* pointer=enemy_script_integer_reference(actor,id);if(!pointer)return false;
    std::memcpy(&value,pointer,4);return true;
}
}

