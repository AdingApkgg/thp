#pragma once
#include "GameOwnerRuntime.hpp"
#include "PlayerReset.hpp"
#include "PlayerEquipmentVisual.hpp"
namespace th143 {
struct GameOwnerStartupHost:PlayerResetHost {
    virtual bool startup_laser_destructor(u32 token)=0;
    virtual bool startup_secondary_visual(i32 child_script,i32 signal)=0;
};
// Root's actual owner reset/activation bodies. Existing allocations, payloads,
// callbacks, SHT and input history remain owned by the shared session.
class GameOwnerStartup final:private PlayerEquipmentHost {
public:
    GameOwnerStartup(GameOwnerRuntime& o,AnmWorld& w,GameOwnerServices& a,GameOwnerStartupHost& h):owners(o),animations(w),services(a),host(h){}
    bool bullets(); //4125c0
    bool player(i32 lives,u32 fragments); //44c440
    bool items(); //419900
    bool lasers(u32 budget=100000); //4322e0
    bool statistics(GameManagerSceneGlobals&); //4554b0
    bool equipment(const PlayerEquipmentGlobals&); //44fde0
private:
    GameOwnerRuntime& owners;AnmWorld& animations;GameOwnerServices& services;GameOwnerStartupHost& host;
    bool retire_resource(u32);
    bool equipment_read(u32 p,u32& v)override{return owners.read(p,&v,4);}
    bool equipment_write(u32 p,u32 v)override{return owners.write(p,&v,4);}
    bool equipment_allocate(u32,u32&,AnmView&)override;
    bool equipment_register(u32,i32,bool,u32,u32&)override{return false;}
    bool equipment_secondary_visual(i32 script,i32 signal)override{return host.startup_secondary_visual(script,signal);}
    bool equipment_visual_initialize(u32 index,AnmView option,const PlayerEquipmentGlobals& g)override{return initialize_equipment_visual(option,index,owners.player,g,animations);}
};
}
