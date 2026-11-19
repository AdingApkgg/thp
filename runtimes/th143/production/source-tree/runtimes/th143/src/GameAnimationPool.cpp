#include "GameAnimationPool.hpp"
namespace th143 {
bool GameAnimationPool::register_pool_callback(u32 entry,i32 priority,bool draw,u32 owner){
    u32 p,result;if(!storage.allocate_game_storage(40,p)||!p||!frames.scheduler.create(p,entry,storage.game_allocation_fill()))return false;
    auto callback=frames.scheduler.at(p);callback.put(4,callback.get(4)|3u);callback.put(0x24,owner);return frames.scheduler.add(p,priority,draw,*this,result);
}
}
