#include "ReplayRecorder.hpp"
using namespace th11;
extern "C" __attribute__((export_name("check"))) u32 check(i32 selection,i32 difficulty,i32 mode){
    ReplayRecorder recorder;
    // Deliberately dirty the optional member as a preceding practice session
    // would. begin() must reset it without changing the requested mode.
    recorder.practice.stage=3;
    recorder.practice_events[1].push_back({0,1});
    if(!recorder.begin(selection/2,selection%2,difficulty,mode!=0,0))return 0xffffffff;
    return u32(recorder.header[10])|(u32(recorder.practice.stage)<<8)|
        (u32(recorder.practice_events[1].size())<<16);
}
