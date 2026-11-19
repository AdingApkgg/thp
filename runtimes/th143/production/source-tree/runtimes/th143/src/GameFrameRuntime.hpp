#pragma once
#include "Scheduler.hpp"
#include "GameInputRuntime.hpp"
#include "PlayerEquipmentFrame.hpp"
#include "PlayerFrame.hpp"
#include "EnemyScripts.hpp"
#include "BulletManager.hpp"
#include "ItemMotion.hpp"
#include "ScorePopups.hpp"
#include "AnmOverlay.hpp"
#include "LaserManager.hpp"
namespace th143 {
struct GameFrameServices {
    virtual ~GameFrameServices()=default;
    // Read live Root/device globals at each callback, including callback35.
    virtual bool frame_input(GameInputFrame&)=0;
    // Session adapters publish/reread shared gameplay globals around a body.
    virtual bool before_game_callback(u32 entry,u32 owner)=0;
    virtual bool after_game_callback(u32 entry,u32 owner,u32 result)=0;
    virtual bool other_game_callback(u32,u32,u32&){return false;}
    virtual bool release_game_callback(u32){return false;}
};
// The application binds owners as Root factories construct them, then uses
// the actual Scheduler for ordering/return codes. Missing bindings fail.
class GameFrameRuntime final:private SchedulerHost {
public:
    explicit GameFrameRuntime(GameFrameServices& services,u32 scheduler_self=0x6e008000):services(services){scheduler.self=scheduler_self;scheduler.construct();}
    Scheduler scheduler;
    AnmWorld* animations=nullptr;AnmOverlay* overlay=nullptr;
    GameInputRuntime* input=nullptr;
    ScorePopups* scores=nullptr;AnmTimerHost* score_host=nullptr;
    PlayerEquipmentState* equipment=nullptr;const u32* fresh=nullptr;PlayerEquipmentFrameHost* equipment_host=nullptr;
    PlayerState* player=nullptr;PlayerFrameGlobals* player_globals=nullptr;PlayerFrameHost* player_host=nullptr;
    EnemyScripts* enemies=nullptr;
    u32 laser_manager=0;LaserManagerHost* laser_host=nullptr;
    const u32* special_flags=nullptr;
    BulletPool* bullets=nullptr;BulletManagerHost* bullet_host=nullptr;
    ItemPool* items=nullptr;ItemPlayer* item_player=nullptr;ItemMotionHost* item_host=nullptr;
    u32 failed_entry=0,failed_owner=0;
    bool register_callback(u32 token,u32 entry,u32 owner,i32 priority,bool draw=false,u32 flags=3);
    bool dispatch(bool draw,i32& result,u32 budget=100000);
private:
    GameFrameServices& services;
    bool invoke(u32,u32,u32&)override;
    bool release_callback(u32 token)override{return services.release_game_callback(token);}
    bool body(u32,u32,u32&);
};
}
