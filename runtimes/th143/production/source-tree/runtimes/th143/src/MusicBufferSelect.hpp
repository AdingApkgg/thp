#pragma once
#include "AnmState.hpp"
namespace th143 {
struct MusicBufferSelectHost {
    virtual ~MusicBufferSelectHost()=default;
    virtual bool music_select_region(u32 token,u32 bytes,AnmView& out)=0;
    virtual bool music_select_status(u32 buffer,u32& status,u32& result)=0;
    virtual bool music_select_random(u32& value)=0;
};
//4862c0: first nonnull nonplaying buffer, otherwise rand()%count (including
// null slots in the fallback). HRESULT from GetStatus is ignored.
bool select_music_buffer(AnmView object,u32 bytes,MusicBufferSelectHost&,u32& buffer);
}
