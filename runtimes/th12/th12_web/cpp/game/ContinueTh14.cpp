#include "ContinueTh14.hpp"
#include <algorithm>
namespace th11 {
#if PORT_TITLE == 14
bool th14_continue_economy(GameEconomy& e,i32& continues)noexcept{
    // Retail 44ae10..44aee9, including the original 447a80 power add.
    // Its return value is unused; a clamp still posts the full-power notice.
    e.lives=2;e.life_fragments=0;e.th14_bombs=2;e.th14_bomb_fragments=0;
    e.power=e.max_power<0?e.max_power:std::max(e.power_step,0);
    bool capped=false;
    if(e.power<e.max_power){
        e.power=wrapping_add(e.power,signed_bits(u32(e.power_step)*4u));
        if(e.power>e.max_power){e.power=e.max_power;capped=true;}
    }
    continues=std::min(wrapping_add(continues,1),9);e.score_units=0;
    return capped;
}
#endif
}
