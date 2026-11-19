#include "PlayerEquipmentWorld.hpp"
namespace th143 {
bool PlayerEquipmentWorld::equipment_secondary_visual(i32 child_script,i32 signal){
    return cheat.data&&signal_cheat_child(cheat,cheat.get(0x2b8),child_script,signal,graphics);
}
bool PlayerEquipmentWorld::equipment_visual_initialize(u32 index,AnmView option,const PlayerEquipmentGlobals& g){
    return initialize_equipment_visual(option,index,player,g,graphics);
}
}
