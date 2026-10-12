#include "../../cpp/game/GameConfig.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static GameConfig config;
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(check) i32 check(const u8* data,u32 size){config.reset();return config.open(data,size);}
API(data) const u8* data(){return config.bytes.data();}
