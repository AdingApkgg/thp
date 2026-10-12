#include "../../cpp/game/GameInput.hpp"
using namespace th11;
static GameInput input;
extern "C" __attribute__((export_name("apply"))) void apply(u32 previous,u32 held){input={};input.held=previous;input.update_normalized(held);}
extern "C" __attribute__((export_name("value"))) u32 value(u32 n){const u32 values[]{input.held,input.previous,input.pressed,input.released};return n<4?values[n]:0;}
