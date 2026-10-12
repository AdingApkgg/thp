#include "../../cpp/game/Interpolation.hpp"
using namespace th11;
extern "C" __attribute__((export_name("run"))) u32 run(i32 mode,u32 di,u32 ei){
 constexpr i32 durations[]={1,7,64};constexpr float elapsed[]={-1,0,.125,.5,.99,1,7,31,64,99};
 const float value=easing(elapsed[ei],durations[di],InterpolationMode(mode));u32 bits;std::memcpy(&bits,&value,4);return bits;
}
