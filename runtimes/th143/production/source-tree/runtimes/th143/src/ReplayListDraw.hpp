#pragma once
#include "AnmState.hpp"
#include <array>
#include <vector>
namespace th143 {
struct ReplayListDrawHost {
 virtual ~ReplayListDrawHost()=default;
 virtual bool replay_draw_read(u32 address,u32& value)=0;
 virtual bool replay_draw_localtime(u32 time_address,std::array<i32,9>&)=0;
 virtual bool replay_draw_line(const std::array<float,3>&,u32 format,const std::vector<u32>& arguments)=0;
};
// Actual449780, with CRT localtime and ASCII variadic output as boundaries.
bool draw_replay_list(AnmView menu,AnmView ascii,ReplayListDrawHost&);
}
