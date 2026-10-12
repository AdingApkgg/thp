#include "../../cpp/game/SpellTiming.hpp"
#include <cstring>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static SpellTiming timing;static u32 flags;
API(begin) u32 begin(double start,u32 input,i32 frames,u32 replay,u32 index,u32 encoded){timing={};timing.index=index;for(u32 n=0;n<20;++n)timing.records[n]=n==index?encoded:n*0xdeaddeadu;flags=input|1;return timing.update(flags,frames,start,replay);}
API(end) u32 end(double now,i32 frames,u32 replay){flags&=~1u;return timing.update(flags,frames,now,replay);}
API(word) u32 word(u32 n){u32 start[2];std::memcpy(start,&timing.start,8);switch(n){case 0:return flags;case 1:return timing.last_frames;case 2:return timing.encoded;case 3:return timing.index;case 4:return start[0];case 5:return start[1];default:return timing.records[n-6];}}
