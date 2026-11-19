#include "ApplicationGameRequests.hpp"
#include <cmath>
namespace th143 {
bool request_application_music_fade(AnmView audio,u32 duration_word,u32 rate_word,u32& result){
    if(!audio.data)return false;const float rate=real(rate_word);float duration=real(duration_word);
    //The original unordered/equality flag test skips division only for ±0;
    //its upper-bound test also leaves NaN and negative rates on the divide path.
    if(rate!=0.f&&!(rate>1.f))duration=duration/rate;
    const u32 parameter=std::isfinite(duration)&&double(duration)>=-2147483648.&&double(duration)<2147483648.?u32(i32(duration)):0x80000000;
    MusicCommandQueue queue;std::memcpy(queue.data.data(),audio.data+0x24f8,queue.data.size());
    if(!queue.enqueue(5,parameter,""))return false;std::memcpy(audio.data+0x24f8,queue.data.data(),queue.data.size());result=0;return true;
}
bool initialize_application_game_mode(AnmView game,u32 mode,u32& result){
    if(!game.data)return false;const u32 previous=game.get(0xc0);if((previous&0x60)!=0x40)game.put(0x1c,0xffffffff);
    result=(previous&~0x60u)|((mode<<5)&0x60);game.put(0xc0,result);return true;
}
}
