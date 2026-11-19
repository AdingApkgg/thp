#include "PlayerEquipmentVisual.hpp"
namespace th143 {
bool initialize_equipment_visual(AnmView option,u32 index,PlayerState& player,
                                 const PlayerEquipmentGlobals& g,AnmWorld& world){
    if(index!=1&&index!=4)return false;
    u32 flags=option.get(0x14);if(!(flags&1)){option.put(0x10,world.global_rate_token());option.put(0x14,flags|1);}
    option.put(8,0);option.put(12,0);option.put(4,0xffffffff);
    option.put(0x1c,0);option.put(0x18,g.initial_count);
    if(index==1){option.put(0x40,20);option.put(0x44,30);option.put(0x48,0);}
    else{option.put(0x2c,60);option.put(0x28,180);}
    u32 handle;if(!world.create_at(player.get(0x10),index==1?8:13,-1,{0,0,0},handle))return false;
    option.put(0x24,handle);
    if(index==1){
        if(!signal_animation(world,handle,5,true))return false;
        const float scale=float(signed_word(g.initial_parameter))/100.f;
        option.put(0x4c,word(scale));option.put(0x50,word(scale+.5f));
        auto vm=world.find(option.get(0x24));if(!vm.data){option.put(0x24,0);return false;}
        vm.put(0x18,vm.get(0x18)|8);vm.put(0x68,word(scale));vm.put(0x6c,word(scale));
    }
    return true;
}
}
