#include "../../cpp/game/Ending.hpp"
#include "../../cpp/game/GameInput.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager animations;
static AnmResource text;
static ScoreFile scores;
static Ending ending(animations,text,scores);
static std::array<u8,12> code;
static std::array<u32,17> result;
static GameInput input;
static std::array<u32,70> input_result;
API(input_init) void input_init(u32 initial){input=GameInput{};input.counts.fill(initial);input.held_frames.fill(initial);}
API(input_run) const u32* input_run(u32 held){
    input.update(held);input_result[0]=input.held;input_result[1]=input.previous;input_result[2]=input.pressed;input_result[3]=input.released;input_result[4]=input.long_repeat;input_result[5]=input.short_repeat;
    std::copy(input.counts.begin(),input.counts.end(),input_result.begin()+6);std::copy(input.held_frames.begin(),input.held_frames.end(),input_result.begin()+38);return input_result.data();
}
API(run) const u32* run(i32 op,i32 duration,i32 wait,u32 seen,u32 held,u32 shoot_frames,u32 pressed,float rate,i32 time,u32 flags,u32 frames,u32 callback){
    animations.rate=rate;ending.fades.effects.clear();ending.active=true;ending.flags=flags;ending.seen=seen;ending.line=3;ending.color=0xffffff;ending.frames=frames;
    ending.elapsed.set(0,&animations.rate);ending.time.set(time,&animations.rate);ending.wait.set(wait,&animations.rate);
    const u16 schedule=op==9?40:0;std::memcpy(code.data(),&schedule,2);code[2]=u8(op);code[3]=4;std::memcpy(code.data()+4,&duration,4);
    code[8]=255;code[9]=255;code[10]=0;code[11]=0;ending.instruction=code.data();ending.end=code.data()+code.size();
    if(!(callback?ending.tick(held,pressed,shoot_frames):ending.update(held,pressed,shoot_frames)))return nullptr;
    result[0]=ending.active;result[1]=u32(ending.instruction-code.data());result[2]=ending.flags;result[3]=u32(ending.line);result[4]=ending.color;result[5]=u32(ending.sounds.size());
    u32 i=6;for(const Timer* t:{&ending.elapsed,&ending.time,&ending.wait}){result[i++]=u32(t->previous);result[i++]=u32(t->current);std::memcpy(&result[i++],&t->fractional,4);}result[15]=ending.frames;result[16]=u32(ending.music_fade);return result.data();
}
static std::array<u32,8> fade_result;
API(fade_words) const u32* fade_words(){
 fade_result.fill(0);fade_result[0]=ending.fades.effects.size();if(!ending.fades.effects.empty()){const auto& f=ending.fades.effects[0];fade_result[1]=u32(f.type);fade_result[2]=u32(f.duration);fade_result[3]=f.color;fade_result[4]=f.priority;fade_result[5]=u32(f.timer.previous);fade_result[6]=u32(f.timer.current);fade_result[7]=float_bits(f.timer.fractional);}return fade_result.data();
}
