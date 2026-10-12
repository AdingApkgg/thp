#include "../../cpp/game/EclOwner.hpp"
#include "../../cpp/game/Rng.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
namespace th11 {u32 g_ecl_last_opcode=0;volatile i32 trace_point=0;}
struct Services:EclServices {
    Rng rng;
    i32 integer(i32)override{return 0;}double floating(i32 id)override{return id==-9987?rng.signed_unit():0;}
    i32* integer_reference(i32)override{return nullptr;}float* float_reference(i32)override{return nullptr;}
    i32 command(EclContext&)override{return -2;}void* allocate(u32 n)override{return std::malloc(n);}void release(void* p)override{std::free(p);}
};
static Services services;
static EclContext context;
static const u8* code;
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(run_case) i32 run_case(const u8* p,const u8* data,u32 time,u32 rate,u32 seed){services.rng={u16(seed),0,0};context={};code=p;context.instruction=reinterpret_cast<const EclInstruction*>(p);context.time=float_bits(time);context.stack.top=128;std::memcpy(context.stack.data,data,768);return context.update(float_bits(rate),services);}
API(rng_value) u32 rng_value(u32 n){return n?services.rng.calls:services.rng.seed;}
API(value) u32 value(u32 n){if(n==0)return float_bits(context.time);if(n==1)return reinterpret_cast<const u8*>(context.instruction)-code;if(n==2)return context.stack.top;u32 v;std::memcpy(&v,context.stack.data+(n-3)*4,4);return v;}
