#pragma once
#include "PlayerEquipment.hpp"
#include "AnmSignal.hpp"
namespace th143 {
// 4582e0/45ae20: the two primary option initializers with real player ANMs.
bool initialize_equipment_visual(AnmView,u32 index,PlayerState&,
                                 const PlayerEquipmentGlobals&,AnmWorld&);
}
