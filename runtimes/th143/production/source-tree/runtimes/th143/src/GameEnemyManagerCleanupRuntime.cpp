#include "GameEnemyManagerCleanupRuntime.hpp"
namespace th143 {
bool GameEnemyManagerCleanupRuntime::write_enemy_memory(u32 p,const void* b,u32 n){
    auto region=[&](u32 base,u8* bytes,u32 size){if(p<base||std::uint64_t(p)+n>std::uint64_t(base)+size)return false;std::memcpy(bytes+p-base,b,n);return true;};
    if(region(GameEnemyRuntime::self,owner.data.data(),owner.data.size())||region(owner.loader_token,owner.loader.data(),owner.loader.size()))return true;
    for(auto& s:owner.storage)if(region(s.token,s.bytes.data(),s.bytes.size()))return true;
    return world.write(p,b,n);
}
}
