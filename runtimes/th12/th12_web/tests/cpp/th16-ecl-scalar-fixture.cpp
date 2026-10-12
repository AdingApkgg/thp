#include "../../cpp/game/EclOwner.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
namespace th11 {u32 g_ecl_last_opcode=0;volatile i32 trace_point=0;}
struct Services:EclServices{
 float rate=1;float scalar_rate()const override{return rate;}
 i32 integer(i32)override{return 0;}double floating(i32)override{return 0;}
 i32* integer_reference(i32)override{return nullptr;}float* float_reference(i32)override{return nullptr;}
 i32 command(EclContext& c)override{return c.instruction->opcode==99?-1:-2;}
 void* allocate(u32 n)override{return std::malloc(n);}void release(void* p)override{std::free(p);}
} services;
static EclContext c;static const u8* code;
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(begin) void begin(const u8* p,float rate,i32 frame_base){c={};code=p;c.instruction=reinterpret_cast<const EclInstruction*>(p);c.stack.top=128;c.stack.frame_base=frame_base;services.rate=rate;for(auto& s:c.th16_scalars)s.value.timer.previous=0;}
API(tick) i32 tick(){return c.update(services.rate,services);}
API(value) u32 value(u32 n){if(n==0)return float_bits(c.time);if(n==1)return reinterpret_cast<const u8*>(c.instruction)-code;if(n==2)return c.stack.top;u32 target;std::memcpy(&target,c.stack.data+c.stack.frame_base+512,4);return target;}
API(slot_word) u32 slot_word(u32 n){const auto& s=c.th16_scalars[n/12];const auto& v=s.value;const u32 w[]={float_bits(v.start[0]),float_bits(v.end[0]),float_bits(v.initial_tangent[0]),float_bits(v.final_tangent[0]),float_bits(s.current),u32(v.timer.previous),u32(v.timer.current),float_bits(v.timer.fractional),0,v.timer.flags,u32(v.duration),u32(v.mode)};return w[n%12];}
