#include "../../cpp/game/Th14MusicFade.hpp"
#include "../../cpp/game/SoundEffects.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static Th14MusicFade fade;
static i32 master;
static u32 action;
API(reset) void reset(i32 frames,i32 level){fade={};fade.begin(frames);master=level;action=0;}
API(tick) u32 tick(){action=fade.tick();return action==2?1:0;}
API(state) u32 state(u32 n){return n==0?u32(fade.remaining):n==1?u32(fade.total):u32(fade.mode);}
API(event_count) u32 event_count(){return action?1:0;}
API(event_kind) u32 event_kind(){return action==2?0:1;}
API(event_value) u32 event_value(){return action==2?0:u32(SoundEffects::adjusted_volume(fade.volume,master,true));}
