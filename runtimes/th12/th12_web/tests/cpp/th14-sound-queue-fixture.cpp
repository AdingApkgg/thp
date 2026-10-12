#include "../../cpp/game/SoundEffects.hpp"
#include <cstdlib>
#include <vector>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
struct Output:SoundOutput {
    std::vector<u32> events;
    void event(u32 kind,u32 id,u32 value=0){events.insert(events.end(),{kind,id-1,value});}
    void sound_stop(u32 id)override{event(0,id);}
    void sound_position(u32 id,u32 value)override{event(1,id,value);}
    void sound_pan(u32 id,i32 value)override{event(2,id,u32(value));}
    void sound_volume(u32 id,i32 value)override{event(3,id,u32(value));}
    void sound_play(u32 id)override{event(4,id,sound_definitions[id-1].play_flags);}
};
static Output output;
static SoundEffects effects(output);
API(reset) void reset(i32 master,u32 enabled,u32 present){effects.reset();output.events.clear();effects.initialized=true;effects.enabled=enabled;effects.master_volume=master;for(u32 n=0;n<sound_voice_count;++n)effects.buffers[n]=present?n+1:0;}
API(operation) void operation(u32 kind,i32 id,i32 pan,float x){if(kind==0)effects.enqueue(id,pan);else if(kind==1)effects.positioned(id,x);else effects.stop(id);}
API(process) void process(){output.events.clear();effects.process();}
API(state) u32 state(u32 kind,u32 index){switch(kind){case 0:return effects.state.indices[index];case 1:return effects.state.counts[index];case 2:return effects.state.pans[index/128][index%128];case 3:return effects.state.metadata[index];default:return 0;}}
API(event_count) u32 event_count(){return output.events.size()/3;}
API(event_value) u32 event_value(u32 index){return output.events[index];}
API(play_flags) u32 play_flags(u32 id){return sound_definitions[id].play_flags;}
API(music_volume) i32 music_volume(i32 volume,i32 master){return SoundEffects::adjusted_volume(volume,master,true);}
