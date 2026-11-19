#include "EnemySpawnDefaults.hpp"
namespace th143 {
void finish_enemy_spawn_defaults(AnmView state,u32 actor_id){
    state.put(0x40c8,1000);state.put(0x4080,3+(actor_id&1));
    if(state.get(0x4084))return;
    static constexpr u8 effects[92]={35,35,35,35,35,31,35,35,35,35,39,35,35,35,35,43,35,35,35,35,35,35,35,35,35,31,35,35,35,35,49,35,35,35,35,48,35,35,35,35,47,35,35,35,35,35,35,35,35,35,35,35,35,31,35,35,39,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,35,31,35,35,35,39,35,35,35,35,35,35,35,43};
    const u32 script=state.get(0x30c);
    state.put(0x4084,state.get(0x308)==2&&script<92?effects[script]:35);
    state.put(0x4088,1);
}
}
