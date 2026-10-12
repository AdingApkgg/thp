#include "../../cpp/game/GameInput.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(sample) u32 sample(u32 held,const u8* buttons,u32 count,i32 x,i32 y,const u8* config){return controller_keys(held,buttons,count,x,y,config);}
