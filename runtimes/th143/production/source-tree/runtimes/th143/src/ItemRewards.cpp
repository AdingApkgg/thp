#include "ItemRewards.hpp"
namespace th143 {
bool ItemRewards::collect_delayed(i32 type,const std::array<float,3>& position,ScorePopups& popups,u32 rate){
    if(type!=13&&type!=14)return false;
    if(type==13)++count;
    i32 points=signed_word(u32(signed_word(count)/10+1)*10);if(points>=1000)points=1000;
    if(!popups.number(position,points,0xffffffff,rate))return false;
    score+=u32(points/10);if(score>=1000000000)score=999999999;return true;
}
}
