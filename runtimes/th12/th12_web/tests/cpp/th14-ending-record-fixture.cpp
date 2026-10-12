#include "../../cpp/game/Ending.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager animations;
static AnmResource text;
static ScoreFile scores;
static Ending ending(animations,text,scores);
API(run) const u8* run(i32 selection,i32 difficulty,i32 continues,u32 initial){
    scores.settings.fill(u8(initial));ending.record_progress(selection,difficulty,continues);
    return scores.settings.data();
}
API(ending_index) i32 ending_index(){return ending.index;}
API(seen) u32 seen(){return ending.seen;}
