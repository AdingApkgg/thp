#pragma once
#include "EnemyManagerSweep.hpp"
#include "GameEnemyRuntime.hpp"
#include "EnemyScripts.hpp"
#include "EnemyDeath.hpp"
#include "SoundQueue.hpp"
namespace th143 {
class GameEnemyManagerSweepRuntime final:public EnemyManagerSweepService,private EnemyManagerSweepHost,private EnemyDeathHost {
public:
    GameEnemyManagerSweepRuntime(GameEnemyRuntime&,EnemyScripts&,AnmWorld&,ItemPool&,Rng&,SoundQueue&);
    ~GameEnemyManagerSweepRuntime();
    bool sweep()override;
private:
    GameEnemyRuntime& manager;EnemyScripts& scripts;AnmWorld& world;ItemPool& items;Rng& random;SoundQueue& audio;
    bool memory(u32,void*,u32,bool);
    bool enemy_cancel_read(u32 p,void* b,u32 n)override{return memory(p,b,n,false);}
    bool enemy_cancel_write(u32 p,const void* b,u32 n)override{return memory(p,const_cast<void*>(b),n,true);}
    bool enemy_cancel_death(u32,i32&)override;
    bool timer_rate(u32 p,float& r)override{return world.timer_rate(p,r);}
    u32 global_rate_token()const override{return world.global_rate_token();}
    bool death_sound(i32 id,float x)override{return audio.request(u32(id),true,x);}
    bool death_resource(i32,u32&)override;
    bool death_script_name(u32,const char*&)override;
    bool death_callback(u32,ActorState&,EclOwner&)override{return false;}
};
}
