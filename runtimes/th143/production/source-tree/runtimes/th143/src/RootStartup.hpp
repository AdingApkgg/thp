#pragma once
#include "RootFrame.hpp"

namespace th143 {
enum class RootStartupService:u32 {
    hud_begin=0x431770,stop_worker=0x403e90,stage_activate=0x40ee20,
    replay_prepare=0x4101d0,replay_transition=0x410320,
    bullets_reset=0x4125c0,player_reset=0x44c440,items_reset=0x419900,
    enemies_reset=0x419a60,lasers_reset=0x4322e0,statistics_begin=0x4554b0,
    equipment_activate=0x44fde0,hud_initialize=0x42c690,music_clear=0x4447e0
};
struct RootStartupGlobals {
    u32 config=0,application_state=0,game_flags=0,frames=0,scene_frames=0;
    std::array<u32,2> statistics_time{};
};
struct RootStartupHost {
    virtual ~RootStartupHost()=default;
    virtual bool startup_read(u32 address,u32&)=0;
    virtual bool startup_write(u32 address,u32)=0;
    virtual bool startup_clock(std::array<u32,2>&)=0;
    virtual bool startup_service(RootStartupService,u32 owner=0)=0;
    virtual bool startup_spawn_main(const std::array<u32,21>&)=0;
    virtual bool startup_signal(u32 handle,i32 signal)=0;
    virtual bool startup_music(i32 mode,u32 track)=0;
};
enum class RootStartupResult:i32 {unsupported=-2,continue_frame=0,return_one=1};
// 432fd0 startup branches only. An error exit returns immediately from the
// frame; the other branches resume at433598. Owner services must be supplied.
RootStartupResult start_root(RootState&,RootStartupGlobals&,RootStartupHost&);
}
