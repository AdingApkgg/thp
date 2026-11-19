#pragma once
#include "GameEnemyRuntime.hpp"
#include "AnmResourceWorld.hpp"
#include "EnemyCleanup.hpp"
namespace th143 {
// Couples the factory-owned ECL program to real script actors. First-start
// empty reset is supported here; restarting live actors needs their combat
// destructor ownership and is rejected until that session binding is supplied.
class GameEnemyStartup final:private EnemyCleanupMemory {
public:
    GameEnemyStartup(GameEnemyRuntime& o,AnmResourceWorld& w,Scheduler& s,EnemyScriptServices& h,EmitterSink& e):scripts(o.program,h,e),owner(o),animations(w),scheduler(s){}
    EnemyScripts scripts;
    bool reset_empty();
    bool spawn_main(u32 difficulty);
    void publish();
private:
    GameEnemyRuntime& owner;AnmResourceWorld& animations;Scheduler& scheduler;
    bool read_enemy_memory(u32 p,void* out,u32 n)override{return owner.read(p,out,n)||animations.read(p,out,n);}
    bool write_enemy_memory(u32,const void*,u32)override;
    bool release_enemy_storage(u32,bool)override{return false;}
    bool find_enemy_visual(u32 h,u32& t)override{return animations.find_enemy_visual(h,t);}
};
}
