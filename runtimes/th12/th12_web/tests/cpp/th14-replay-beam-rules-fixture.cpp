#include "../../cpp/game/ReplayRecorder.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static Replay replay;
static std::vector<u8> recording;
API(viewer_alloc) void* allocate(u32 size){return std::malloc(size);}
API(viewer_free) void release(void* p){std::free(p);}
API(policy_open) i32 policy_open(const u8* p,u32 size){return replay.open(p,size)?i32(replay.uses_bounded_th14_beams()):-1;}
API(policy_retain) u32 policy_retain(){replay.retain_metadata();return replay.uses_bounded_th14_beams();}
API(policy_record) u32 policy_record(u32 touch){
    ReplayRecorder recorder;ReplayStageState stage{};stage.seed=123;stage.scalars=true;stage.power=100;stage.lives=2;
    if(!recorder.begin(1,1,1,false,0)||!recorder.start_stage(1,stage,true)||
       !recorder.tick(1,1,0,60,touch?1:0,12,34)||!recorder.finish_stage(true)||
       !recorder.save("RULES",0,1,0,0,recording))return 0;
    return u32(recording.size());
}
API(policy_record_data) const u8* policy_record_data(){return recording.data();}
