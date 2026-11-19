#pragma once
#include "ScorePopups.hpp"
namespace th143 {
struct ItemRewards {
    u32 count=0,score=0,chain=0;
    void homing(i32 type){if(type!=9&&type!=10&&type!=11)chain=8;}
    bool collect_delayed(i32 type,const std::array<float,3>& position,ScorePopups&,u32 rate_token);
};
}
