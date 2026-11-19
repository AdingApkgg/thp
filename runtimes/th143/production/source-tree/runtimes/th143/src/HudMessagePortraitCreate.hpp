#pragma once
#include "AnmState.hpp"
namespace th143 {
struct HudMessagePortraitResources {u32 player_index,player_resource,scene_descriptor,enemy_manager;};
struct HudMessagePortraitCreateHost {
 virtual ~HudMessagePortraitCreateHost()=default;
 virtual bool portrait_read_word(u32 address,u32& value)=0;
 virtual bool portrait_create(u32 resource,i32 script,u32& handle)=0;
};
bool create_hud_message_portrait(AnmView,u8,const u8*,u32,const HudMessagePortraitResources&,HudMessagePortraitCreateHost&);
}
