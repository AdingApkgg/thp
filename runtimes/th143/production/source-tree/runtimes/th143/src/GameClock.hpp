#pragma once
#include "AnmState.hpp"

namespace th143 {
struct GameClockHost {
    virtual ~GameClockHost()=default;
    virtual bool performance_counter(std::uint64_t&)=0;
    virtual bool millisecond_ticks(u32&)=0;
};
// 46f4e0. Host supplies OS clock readings, not the game's elapsed result.
struct GameClock {
    std::uint64_t frequency=0,base_counter=0;
    double origin=0;
    bool sample(GameClockHost&,double&);
};
}
