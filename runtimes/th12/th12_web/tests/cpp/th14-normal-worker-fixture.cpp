// The host supplies a clock observation at normal ANM entry. The production
// stage loader performs Replay restoration; VM callbacks are never wrapped.
#include "th14-native-campaign-fixture.cpp"
namespace {
u32 normal_clock_callback=0,normal_clock_delivery_count=0;
u64 normal_clock_ready_ns=0;
bool normal_clock_failed=false;
std::function<u64()> normal_clock_previous;
}
API(observed_normal_clock) u32 observed_normal_clock(u32 callback,u64 now){
    if(normal_clock_callback||!callback||now<probe_clock_ns||!session.battle)return 0;
    normal_clock_callback=callback;normal_clock_ready_ns=now;
    normal_clock_previous=session.stage_load_clock;
    session.stage_load_clock=[](){
        if(!normal_clock_delivery_count&&public_player_observations==normal_clock_callback){
            if(probe_clock_ns>normal_clock_ready_ns)normal_clock_failed=true;
            else probe_clock_ns=normal_clock_ready_ns;
            ++normal_clock_delivery_count;
        }
        return normal_clock_previous();
    };
    return 1;
}
API(observed_normal_clock_state) u32 observed_normal_clock_state(u32 field){
    return field==0?normal_clock_delivery_count:normal_clock_failed;
}
