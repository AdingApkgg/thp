#pragma once
#include "GameOwnerRuntime.hpp"
namespace th143 {
//42bcd0/42bd30. The framework owns this draw-only timing/statistics object;
//455420 reads its+34 even during update-only gameplay/recording sessions.
// Actual42bf70 rendering/time sampling is a separate draw service.
class GameFrameTimingRuntime final:private SchedulerHost {
public:
    static constexpr u32 self=0x6b00a000;
    GameFrameTimingRuntime(Scheduler& s,GameOwnerServices& a):scheduler(s),services(a){}
    std::array<u8,0x8c> data{};
    u32 global_owner=0;
    AnmView view(){return {data.data()};}
    bool create(u32& result);
    bool destroy();
private:
    Scheduler& scheduler;GameOwnerServices& services;
    bool invoke(u32,u32,u32&)override{return false;}
    bool release_callback(u32 p)override{return services.release_game_storage(p);}
};
}
