#pragma once
#include "EnemyManagerCleanup.hpp"
#include "GameEnemyCleanupRuntime.hpp"
namespace th143 {
// Compose41ea20 with the live actor/ECL reset,Scheduler and resource world.
// Released typed storage remains readable for continuous-session auditing.
class GameEnemyManagerCleanupRuntime final:private EnemyManagerCleanupHost,private SchedulerHost {
public:
    GameEnemyManagerCleanupRuntime(GameEnemyRuntime& o,GameEnemyCleanupRuntime& a,AnmResourceWorld& w,Scheduler& q):owner(o),actors(a),world(w),scheduler(q){}
    bool cleanup(){return owner.global_owner&&cleanup_enemy_manager(owner.view(),GameEnemyRuntime::self,owner.global_owner,*this);}
private:
    GameEnemyRuntime& owner;GameEnemyCleanupRuntime& actors;AnmResourceWorld& world;Scheduler& scheduler;
    bool reset_enemy_manager(u32 p)override{return p==GameEnemyRuntime::self&&actors.reset();}
    bool remove_enemy_manager_callback(u32 p)override{return scheduler.remove(p,*this);}
    bool unload_enemy_animation(u32 slot)override{return world.unload(slot);}
    bool read_enemy_memory(u32 p,void* b,u32 n)override{return owner.read(p,b,n)||world.read(p,b,n);}
    bool write_enemy_memory(u32 p,const void* b,u32 n)override;
    bool release_enemy_storage(u32 p,bool array)override{return world.release_enemy_storage(p,array);}
    bool find_enemy_visual(u32 h,u32& p)override{return world.find_enemy_visual(h,p);}
    bool invoke(u32,u32,u32&)override{return false;}
    bool release_callback(u32 p)override{return world.release_enemy_storage(p,false);}
};
}
