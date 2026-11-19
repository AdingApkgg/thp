#include "GameClock.hpp"
#include <cstring>

namespace th143 {
namespace {
double signed_double(std::uint64_t v){std::int64_t s;std::memcpy(&s,&v,8);return double(s);}
}
bool GameClock::sample(GameClockHost& host,double& result){
    if(frequency){
        std::uint64_t counter;if(!host.performance_counter(counter))return false;
        const double now=signed_double(counter-base_counter)/signed_double(frequency);
        if(origin>now)origin=now;result=now-origin;
    }else{
        u32 ticks;if(!host.millisecond_ticks(ticks))return false;
        const double now=double(ticks);if(origin>now)origin=now;
        // Retain the original fallback's multiplication/subtraction order.
        result=(now-origin*1000.0)/1000.0;
    }return true;
}
}
