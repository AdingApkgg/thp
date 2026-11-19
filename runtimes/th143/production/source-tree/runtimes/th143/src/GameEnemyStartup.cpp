#include "GameEnemyStartup.hpp"
namespace th143 {
bool GameEnemyStartup::write_enemy_memory(u32 p,const void* data,u32 n){
    if(p>=GameEnemyRuntime::self&&p-GameEnemyRuntime::self<=owner.data.size()&&n<=owner.data.size()-(p-GameEnemyRuntime::self)){std::memcpy(owner.data.data()+p-GameEnemyRuntime::self,data,n);return true;}
    for(auto& [base,b]:scheduler.records)if(p>=base&&p-base<=b.size()&&n<=b.size()-(p-base)){std::memcpy(b.data()+p-base,data,n);return true;}return animations.write(p,data,n);
}
bool GameEnemyStartup::reset_empty(){
    if(!owner.global_owner||!scripts.live.empty()||owner.view().get(0xd0))return false;
    std::array<u32,6> resources{};for(const auto& r:animations.resources)if(r.file>=10&&r.file<16)resources[r.file-10]=r.token;
    return reset_enemies(GameEnemyRuntime::self,resources,{animations.instances.registry.primary_head,animations.instances.registry.secondary_head},*this);
}
void GameEnemyStartup::publish(){
    auto v=owner.view();v.put(0xdc,scripts.next_id);v.put(0xe0,scripts.last_id);v.put(0x9c,scripts.controls.flags);
    for(u32 i=0;i<scripts.controls.bosses.size();++i)v.put(0x5c+i*4,scripts.controls.bosses[i]);
    v.put(0xd0,scripts.live.empty()?0:scripts.live.front()->token+0x157c);v.put(0xd4,scripts.live.empty()?0:scripts.live.back()->token+0x157c);v.put(0xd8,u32(scripts.live.size()));
}
bool GameEnemyStartup::spawn_main(u32 difficulty){
    if(!owner.global_owner||scripts.failed||!scripts.storage.empty())return false;
    scripts.next_id=owner.view().get(0xdc);scripts.last_id=owner.view().get(0xe0);scripts.difficulty=difficulty;
    if(!scripts.spawn_enemy("main",{}))return false;publish();return animations.synchronize_resources();
}
}
