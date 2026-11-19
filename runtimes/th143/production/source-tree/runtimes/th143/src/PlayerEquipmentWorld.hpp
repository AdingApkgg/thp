#pragma once
#include "PlayerEquipmentVisual.hpp"
#include "CheatAnimation.hpp"
namespace th143 {
// Share the resource-backed ANM world for primary option visuals and the
// selected CheatManager UI children. Allocation/callback ownership is supplied
// by the session storage host used for the equipment owner itself.
class PlayerEquipmentWorld:public PlayerEquipmentHost {
public:
    PlayerEquipmentHost& storage;PlayerState& player;AnmView cheat;AnmWorld& graphics;
    PlayerEquipmentWorld(PlayerEquipmentHost& s,PlayerState& p,AnmView c,AnmWorld& w):storage(s),player(p),cheat(c),graphics(w){}
    bool equipment_read(u32 p,u32& value)override{return storage.equipment_read(p,value);}
    bool equipment_write(u32 p,u32 value)override{return storage.equipment_write(p,value);}
    bool equipment_allocate(u32 n,u32& token,AnmView& view)override{return storage.equipment_allocate(n,token,view);}
    bool equipment_register(u32 entry,i32 priority,bool draw,u32 self,u32& token)override{return storage.equipment_register(entry,priority,draw,self,token);}
    bool equipment_secondary_visual(i32 child_script,i32 signal)override;
    bool equipment_visual_initialize(u32 index,AnmView,const PlayerEquipmentGlobals&)override;
};
}
