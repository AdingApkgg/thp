#include "EnemyClockVariables.hpp"
namespace th143 {
bool enemy_clock_variable(AnmView actor,i32 id,i32& value){if(!actor.data)return false;const u32 offset=id==-9988?0x360:id==-9986?0x374:0;if(!offset)return false;value=signed_word(actor.get(offset));return true;}
}
