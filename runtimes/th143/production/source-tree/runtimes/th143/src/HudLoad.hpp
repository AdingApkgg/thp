#pragma once
#include "AnmState.hpp"
namespace th143 {
struct HudLoadGlobals {u32 descriptor=0,pending_file=0,score=0;};
struct HudLoadHost {
    virtual ~HudLoadHost()=default;
    virtual bool hud_load_read(u32 token,void*,u32 bytes)=0;
    virtual bool hud_load_write(u32 token,const void*,u32 bytes)=0;
    virtual bool load_hud_scene_animation(u32 name,u32& resource)=0;
    virtual bool read_hud_message_file(u32 name,u32& file)=0;
    virtual bool hud_load_error()=0;
    virtual bool hud_cached_file_log(u32 name)=0;
};
//42c4e0. Resource/message-file services are owned by the application adapter;
// incoming cached file ownership and all HUD/timer fields are updated here.
bool load_hud_scene(AnmView,HudLoadGlobals&,HudLoadHost&,i32& result);
}
