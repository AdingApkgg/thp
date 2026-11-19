#pragma once
#include "AnmVm.hpp"
#include <array>
namespace th143 {
class ScorePopups {
public:
    static constexpr u32 bytes=0xf2c,token=0x69000000;
    std::array<u8,bytes> data{};
    u32 get(u32 at)const;
    void put(u32 at,u32 value);
    void construct();
    bool initialize(u32 resource,AnmVmHost&);
    bool number(const std::array<float,3>& position,i32 value,u32 color,u32 rate_token);
    bool update(AnmTimerHost&);
};
}
