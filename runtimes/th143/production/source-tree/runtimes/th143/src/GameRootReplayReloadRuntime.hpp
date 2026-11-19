#pragma once
#include "RootLoad.hpp"
#include "GameRootReplayLoadRuntime.hpp"
#include "GameStageRuntime.hpp"
#include "GameHudRuntime.hpp"
#include "GameMenuRuntime.hpp"
#include "GameEnemyRuntime.hpp"
#include "GameCheatRuntime.hpp"
#include "GameAuxRuntime.hpp"
#include "GameFrameTimingRuntime.hpp"
namespace th143 {
//432440 reload after verified teardown; retains an empty EnemyManager and
// consumes the existing SHT allocation through original44bd00 cached branch.
// The platform retains application/audio/clock services and immutable address
// inputs. It cannot substitute the gameplay factories handled here.
class GameRootReplayReloadRuntime final:private RootLoadHost,private SchedulerHost {
public:
    GameRootReplayReloadRuntime(RootState&,u32,GameManagerInitGlobals&,SaveData&,u32,
        GameFrameRuntime&,GameOwnerRuntime&,GameStageRuntime&,GameHudRuntime&,
        GameMenuRuntime&,GameEnemyRuntime&,GameCheatRuntime&,GameAuxRuntime&,
        GameFrameTimingRuntime&,AnmResourceWorld&,GameOwnerServices&,RootLoadHost&,GameRootReplayInputHost&);
    bool load(i32& result,u32 wait_budget=100000);
    u32 cached_shots=0; // shared original4e6b8c
    u32 last_entry=0,last_address=0;
private:
    RootState& root;u32 self;GameManagerInitGlobals& state;SaveData& save;u32 save_token;
    GameFrameRuntime& frames;GameOwnerRuntime& owners;GameStageRuntime& stage;
    GameHudRuntime& hud;GameMenuRuntime& menu;GameEnemyRuntime& enemies;
    GameCheatRuntime& cheat;GameAuxRuntime& auxiliary;GameFrameTimingRuntime& timing;
    AnmResourceWorld& animations;GameOwnerServices& storage;RootLoadHost& platform;GameRootReplayInputHost& replay_input;
    bool map(u32,void*,u32,bool);
    bool name(u32,std::string&);
    bool load_read(u32 p,void* out,u32 n)override{return map(p,out,n,false);}
    bool load_write(u32 p,const void* in,u32 n)override{return map(p,const_cast<void*>(in),n,true);}
    bool load_call(u32,u32,std::initializer_list<u32>,u32&)override;
    bool load_signal(u32 p,i32 s,bool immediate)override{return platform.load_signal(p,s,immediate);}
    bool load_sleep(u32 ms)override{return platform.load_sleep(ms);}
    bool load_float_environment()override{return platform.load_float_environment();}
    bool invoke(u32,u32,u32&)override{return false;}
    bool release_callback(u32 p)override{return storage.release_game_storage(p);}
};
}
