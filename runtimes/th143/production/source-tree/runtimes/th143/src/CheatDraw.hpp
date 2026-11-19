#pragma once
#include "CheatScene.hpp"
namespace th143 {
struct CheatDrawHost {
    virtual ~CheatDrawHost()=default;
    // Format strings are the original ASCII formats. Number is the separate
    // 40b810 numeric renderer; format is the40b7c0 formatted-text boundary.
    virtual bool cheat_draw_format(const std::array<float,3>&,const char*,double value)=0;
    virtual bool cheat_draw_number(const std::array<float,3>&,i32 value)=0;
};
// 437e40. ASCII queue generation is delegated; style/position/save selection
// and the original numeric arithmetic execute here.
bool draw_cheat_owner(AnmView owner,AnmView save,AnmView ascii,AnmWorld&,CheatDrawHost&);
}
