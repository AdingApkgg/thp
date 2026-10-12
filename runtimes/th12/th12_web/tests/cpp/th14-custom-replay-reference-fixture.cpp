#include "th14-session-reference-fixture.cpp"
API(begin_custom_reference) u32 begin_custom_reference(const u8* data,u32 size){
    if(!session.begin_replay(source,data,size,0,true))return 0;
    reference_rng_reads.clear();session.battle->before_player_update=observe_reference;return 1;
}
