#include "EnemyPositionClampDisable.hpp"
namespace th143 {
bool disable_enemy_position_clamp(AnmView actor){if(!actor.data)return false;actor.put(0x4100,actor.get(0x4100)&0xfffdffffu);return true;}
}
