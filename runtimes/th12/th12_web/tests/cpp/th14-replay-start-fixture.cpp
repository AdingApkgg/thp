#include "../../cpp/game/Replay.hpp"
#include "../../cpp/game/ReplayRecorder.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static u8 input[0xdc];static ReplayRecorder recorder;
API(input_header) u8* input_header(){return input;}
API(capture) u32 capture(){ReplayStageState s;s.read(input);return recorder.begin(0,0,1,false,0)&&recorder.start_stage(u32(input[0])|u32(input[1])<<8,s,false);}
API(output_header) const u8* output_header(){return recorder.stages[u32(input[0])|u32(input[1])<<8].header.data();}
