#pragma once
#include "AnmState.hpp"
#include <array>
#include <vector>

namespace th143 {
struct PauseMenuHost {
    virtual ~PauseMenuHost()=default;
    virtual bool bind(AnmView,u32 self,i32 script)=0;
};
struct PauseMenu {
    static constexpr u32 bytes=0x91c4;
    std::array<u8,bytes> data{};
    std::vector<u8> hints;
    u32 self=0x6b000000;
    AnmView view(){return {data.data()};}
    void construct();
    // Original4477d0: raw private hint.txt, callback ownership and two embedded
    // resolution-dependent ANMs. Hint strings remain original encoded bytes.
    bool initialize(const u8* raw,u32 n,u32 hint_token,u32 update_token,u32 draw_token,u32 width,PauseMenuHost&,u32 rate_token=0x4e40b0);
    void state(i32 value,u32 rate_token=0x4e40b0);
    void substate(i32 value,u32 rate_token=0x4e40b0);
};
}
