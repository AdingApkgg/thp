#include "../../cpp/game/GraphicsMath.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static Vec3 value;
API(run) void run(u32 x,u32 y,u32 z){Vec3 v;std::memcpy(&v.x,&x,4);std::memcpy(&v.y,&y,4);std::memcpy(&v.z,&z,4);value=GraphicsMath::normalize(v);}
API(word) u32 word(u32 n){u32 b;float f=n==0?value.x:n==1?value.y:value.z;std::memcpy(&b,&f,4);return b;}
