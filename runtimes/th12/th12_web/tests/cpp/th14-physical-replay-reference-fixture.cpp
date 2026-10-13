#include "th14-custom-replay-reference-fixture.cpp"
static u32 physical_observations=0;
API(begin_physical_reference) u32 begin_physical_reference(const u8* data,u32 size){
    if(!begin_custom_reference(data,size))return 0;
    physical_observations=0;
    session.battle->before_player_update=[](const GameBattle& battle){
        ++physical_observations;observe_reference(battle);
    };
    return 1;
}
API(physical_observation_count) u32 physical_observation_count(){return physical_observations;}
