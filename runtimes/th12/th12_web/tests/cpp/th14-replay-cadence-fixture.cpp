#include "../../cpp/game/ReplayCadenceTh14.hpp"
#include "../../cpp/game/ReplayRecorder.hpp"
#define API(name) extern "C" __attribute__((export_name(#name)))
extern "C" __attribute__((export_name("repeat")))
unsigned repeat(unsigned controller,unsigned mode,unsigned flags,unsigned held,unsigned frame){
    return th11::th14_replay_repeat(controller,mode,flags,held,frame)?6:1;
}
static th11::Replay playback;
static std::vector<th11::u8> bytes;
API(start) unsigned start(){
    th11::ReplayRecorder writer;th11::ReplayStageState state;
    if(!writer.begin(0,0,1,false,0))return 0;
    if(!writer.start_stage(1,state,true)||!writer.tick(1,1,0)||!writer.tick(0,0,1)||!writer.finish_stage())return 0;
    if(!writer.start_stage(2,state,false)||!writer.tick(1,1,0)||!writer.finish_stage(true))return 0;
    if(!writer.save("CADENCE",0,2,0,0,bytes))return 0;
    return playback.open(bytes.data(),th11::u32(bytes.size()));
}
API(select_stage) unsigned select_stage(unsigned stage){return playback.select(stage);}
API(tick) unsigned tick(unsigned active){return playback.tick(active).end_marker;}
API(frame) unsigned frame(){return playback.frame();}
API(callback_frame) unsigned callback_frame(){return playback.callback_frame();}
API(reopen) unsigned reopen(){return playback.open(bytes.data(),th11::u32(bytes.size()));}
