#include "EnemyBossCounterTransfer.hpp"
namespace th143 {i32 transfer_enemy_boss_counter(AnmView source,AnmView boss){if(boss.data)boss.put(0x407c,source.get(0x32c));return 0;}}
