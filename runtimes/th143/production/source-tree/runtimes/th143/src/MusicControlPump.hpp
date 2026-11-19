#pragma once
#include "AnmState.hpp"
namespace th143 {
struct MusicControlPumpHost {
    virtual ~MusicControlPumpHost()=default;
    virtual bool music_control_object(u32 token,AnmView& object,u32& bytes)=0;
    virtual bool music_control_call(u32 entry,u32 object,const u32* args,u32 count)=0;
};
//472df0 through the pre-SFX473267 boundary, commands5/6/7/8 only.
// The returned logical scratch is the actual post-compaction queue cursor.
bool pump_music_control(AnmView audio,u32 bytes,u8 music_enabled,
                       MusicControlPumpHost&,bool& reached_sfx,u32& scratch);
}
