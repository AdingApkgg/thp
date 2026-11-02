#include "ScreenShake.hpp"
using namespace th11;
static u32 output[11];
extern "C" u32 stack_case(u32 phased,float rate,u32 seed,i32 timer,u32 prior){
 ScreenShakes shakes;ScreenShake effect;effect.duration=48;effect.start=phased?6:12;effect.end=0;
 effect.phased=phased;effect.ramp=17;effect.hold=31;effect.fall=3;effect.timer.set(timer,&rate);
 shakes.effects.push_back(effect);shakes.offset={3,-5};Rng script{u16(seed)},visual{u16(seed)};
 NativeStackTh14 stack;stack.controller_scratch=prior;
 shakes.update(script,false,&visual,&stack);const auto& rng=phased?visual:script;
 output[0]=stack.controller_scratch;output[1]=stack.controller_scratch_known;output[2]=shakes.effects.empty()?7:1;
 output[3]=rng.seed;output[4]=rng.calls;
 if(!shakes.effects.empty()){const auto& t=shakes.effects[0].timer;output[5]=u32(t.previous);output[6]=u32(t.current);std::memcpy(&output[7],&t.fractional,4);}
 std::memcpy(&output[8],&shakes.offset.x,4);std::memcpy(&output[9],&shakes.offset.y,4);output[10]=u32(shakes.effects.size());
 return u32(reinterpret_cast<uintptr_t>(output));
}
