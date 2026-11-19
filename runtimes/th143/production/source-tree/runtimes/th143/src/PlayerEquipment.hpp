#pragma once
#include "PlayerState.hpp"
#include "AnmState.hpp"

namespace th143 {
struct PlayerEquipmentState {
    std::array<u8,0x3c> data{};
    AnmView view(){return {data.data()};}
    void construct(){data.fill(0);view().put(0,2);}
};
struct PlayerEquipmentGlobals {
    u32 primary=0,secondary=0,alternate=0,initial_count=0,initial_parameter=0;
};
struct PlayerEquipmentHost {
    virtual ~PlayerEquipmentHost()=default;
    virtual bool equipment_read(u32,u32&)=0;
    virtual bool equipment_write(u32,u32)=0;
    virtual bool equipment_allocate(u32 bytes,u32& token,AnmView&)=0;
    virtual bool equipment_register(u32 entry,i32 priority,bool draw,u32 self,u32& token)=0;
    virtual bool equipment_secondary_visual(i32 child_script,i32 signal){return false;}
    virtual bool equipment_visual_initialize(u32 index,AnmView,const PlayerEquipmentGlobals&){return false;}
};
bool initialize_player_equipment(PlayerEquipmentState&,u32 self,PlayerEquipmentHost&); //44fd40
// 44fde0. Primary1/4 require equipment_visual_initialize; the resource-backed
// implementation is supplied by PlayerEquipmentVisual. Missing services fail.
bool activate_player_equipment(PlayerEquipmentState&,PlayerState&,
                               const PlayerEquipmentGlobals&,PlayerEquipmentHost&);
}
