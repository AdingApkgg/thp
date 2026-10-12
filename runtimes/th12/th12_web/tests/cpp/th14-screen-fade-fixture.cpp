#include "../../cpp/game/ScreenFade.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static ScreenFade effect;static float rate;
API(initialize) void initialize(i32 type,i32 duration,float speed){rate=speed;effect={};effect.type=type;effect.duration=duration;effect.alpha=type==3?255:0;effect.timer.set(0,&rate);}
API(tick) i32 tick(i32 stopped,i32 frozen){return effect.update(stopped,frozen);}
API(value) u32 value(u32 n){u32 frac;std::memcpy(&frac,&effect.timer.fractional,4);const u32 words[]={u32(effect.alpha),u32(effect.timer.previous),u32(effect.timer.current),frac};return n<4?words[n]:0;}
