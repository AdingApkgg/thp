#include "../../cpp/game/ContinueTh14.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static GameEconomy economy;static i32 count;
API(run) i32 run(i32 maximum,i32 step,i32 continues,i32 fragments){
    economy={};economy.lives=-1;economy.life_fragments=2;economy.th14_bombs=0;economy.th14_bomb_fragments=fragments;
    economy.score_units=123456;economy.power=7;economy.max_power=maximum;economy.power_step=step;count=continues;
    economy.point_value=3456;economy.graze=789;economy.rank=-512;economy.th14_point_items=17;economy.th14_life_awards=2;
    return th14_continue_economy(economy,count);
}
API(value) i32 value(u32 n){
    const i32 values[]={economy.lives,economy.life_fragments,economy.th14_bombs,economy.th14_bomb_fragments,economy.power,count,economy.score_units,
        economy.point_value,economy.graze,economy.rank,economy.th14_point_items,economy.th14_life_awards};return n<12?values[n]:0;
}
