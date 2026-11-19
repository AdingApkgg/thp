#pragma once
#include "PlayerEquipment.hpp"
namespace th143 {
struct PlayerEquipmentFrameHost:AnmTimerHost {
    virtual bool update_equipment_option(u32 token)=0;
    virtual bool draw_equipment_option(u32 token)=0;
    virtual bool equipment_option_busy(u32 token,bool&)=0;
    virtual bool equipment_option_count(u32 token,u32&)=0;
    virtual bool equipment_empty_sound(u32 id)=0;
};
// Fresh input is read after virtual updates; callbacks can consume it.
bool update_player_equipment(PlayerEquipmentState&,float rate,const u32& fresh,PlayerEquipmentFrameHost&); //450700
bool draw_player_equipment(PlayerEquipmentState&,PlayerEquipmentFrameHost&); //450830/4507f0
}
