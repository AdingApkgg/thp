#include "EnemyActorExists.hpp"
namespace th143 {
u32 enemy_actor_exists(const EnemyActorIdentityEntry* entries,u32 count,u32 id){
 if(!id)return 0;for(u32 i=0;i<count;++i)if(entries[i].id==id)return 1;return 0;
}
}
