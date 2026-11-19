#include "BulletClearAll.hpp"
namespace th143 {
bool clear_all_bullets(BulletPool& pool,const float& elapsed,BulletCancelGlobals& globals,AnmWorld& world,BulletCancelHost& host){
    for(u32 i=0;i<BulletPool::count;++i){
        BulletView bullet{pool.data.data()+BulletPool::first+i*BulletPool::stride};
        if(bullet.state()==0||bullet.state()==3)continue;
        if(!cancel_bullet(bullet,0,pool.get(0x9bf6cc),elapsed,globals,world,host))return false;
    }
    return true;
}
}
