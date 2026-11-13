#include "ReplayDescriptionTh14.hpp"
#include <cstdlib>
using namespace th11;
#define API(n) extern "C" __attribute__((export_name(#n)))
static std::string output,error;
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(describe) const char* describe(const u8* data,u32 size){return describe_replay_th14(data,size,output,error)?output.c_str():nullptr;}
API(error_data) const char* error_data(){return error.c_str();}
