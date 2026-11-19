#include "EnemyMotionVariables.hpp"
namespace th143 {
bool enemy_motion_variable(AnmView actor,i32 id,float& value){u32 at;switch(id){case -9997:case -9977:at=0x44;break;case -9996:case -9976:at=0x48;break;case -9975:at=0x88;break;case -9974:at=0x8c;break;case -9973:at=0xcc;break;case -9972:at=0xd0;break;case -9971:at=0xa4;break;case -9970:at=0xe8;break;default:return false;}value=actor.floating(at);return true;}
}
