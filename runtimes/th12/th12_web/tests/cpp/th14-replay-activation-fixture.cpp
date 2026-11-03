#include "th14-replay-cadence-fixture.cpp"
API(start_phase) unsigned start_phase(unsigned phase,unsigned target){
    if(phase>30||target<1||target>7)return 0;
    th11::ReplayRecorder writer;th11::ReplayStageState state;std::vector<th11::u8> data;
    const unsigned first=target==1?2:1;
    if(!writer.begin(0,0,1,false,0)||!writer.start_stage(first,state,true))return 0;
    for(unsigned i=0;i<phase;++i)if(!writer.tick(0,0,0))return 0;
    if(!writer.finish_stage()||!writer.start_stage(target,state,false))return 0;
    for(unsigned i=0;i<64;++i)if(!writer.tick(0,0,0))return 0;
    if(!writer.finish_stage())return 0;
    writer.stages[target].fps={17,33,49,65,81,97,113,129};
    if(!writer.save("ACTIVATE",0,2,0,0,data)||!playback.open(data.data(),th11::u32(data.size()))||!playback.select(first))return 0;
    for(unsigned i=0;i<phase;++i)playback.tick();
    return playback.callback_frame()==phase;
}
API(step_fps) unsigned step_fps(){return playback.tick().fps;}
