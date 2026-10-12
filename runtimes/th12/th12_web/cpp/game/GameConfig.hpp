#pragma once
#include "Types.hpp"
#include "PortTitle.hpp"
#include <array>
namespace th11 {
// Original fixed-size th11.cfg. Platform-specific display fields are retained
// when imported, while the SDL backend owns its actual window and swap chain.
struct GameConfig {
    std::array<u8,kPortTitle==14?0x5c:0x3c> bytes{};
    static constexpr u32 volume_offset=kPortTitle==14?0x22:0x20;
    GameConfig(){reset();}
    void reset(const u8* controller=nullptr)noexcept;
    bool open(const u8*,u32)noexcept;
    i32 music_volume()const noexcept{return bytes[volume_offset];}
    i32 sound_volume()const noexcept{return bytes[volume_offset+1];}
    bool auto_focus()const noexcept{return bytes[volume_offset+2]!=0;}
};
}
