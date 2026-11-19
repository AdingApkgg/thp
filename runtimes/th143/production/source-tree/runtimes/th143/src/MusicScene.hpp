#pragma once
#include "MusicCommandQueue.hpp"
namespace th143 {
// CPU-only scene music load and the no-BGM/no-playback-object branch of the
// main-thread pump. This preserves queued commands and cached names; a real
// audio object or unsupported command rejects instead of pretending to play.
struct MusicScene {
    static constexpr u32 path_count=16,path_bytes=256;
    std::array<u8,path_count*path_bytes> paths{};
    bool load(MusicCommandQueue&,const char* name); //444660
    bool pump_silent(MusicCommandQueue&,bool wrapper_present,bool bgm_enabled,bool playback_present); //472df0/4726a0
};
}
