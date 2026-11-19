#include "EnemyActorLookup.hpp"
namespace th143 {
u32 enemy_actor_lookup(const EnemyActorIdentityEntry* entries,u32 count,u32 id){
 if(!id)return 0;u32 result=0;for(u32 i=0;i<count;++i){result=entries[i].token;if(entries[i].id==id)break;}return result;
}
}
