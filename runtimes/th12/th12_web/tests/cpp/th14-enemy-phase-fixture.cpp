#include "../../cpp/game/EnemyState.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static u32 output[23];
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(run) void run(const u32* input){
    EnemyState e{};float rate=1;e.health=i32(input[0]);e.flags=input[2];
    const i32 elapsed=i32(input[1]);e.timer_2bc={elapsed-1,elapsed,float(elapsed),input[6]?&rate:nullptr,input[6]};
    e.lifetime.set(999,&rate);
    for(u32 n=0;n<8;++n){const auto* p=input+7+n*4;e.interrupts[n]={i32(p[0]),i32(p[1]),reinterpret_cast<const char*>(p[2]),reinterpret_cast<const char*>(p[3])};}
    i32 seconds=777,hundredths=888,spell_elapsed=i32(input[4]),bonus=999,shared=123;u32 sf=input[3];
    EnemyPhaseState phase{&rate,&seconds,&hundredths,&sf,&spell_elapsed,&bonus,&shared,i32(input[5]),2,1};
    const char* result=e.check_interrupts(phase);
    const u32 values[]={u32(result),u32(e.health),u32(e.interrupt_health),u32(e.health_baseline),e.flags,
      u32(e.timer_2bc.previous),u32(e.timer_2bc.current),float_bits(e.timer_2bc.fractional),e.timer_2bc.rate?1u:0u,e.timer_2bc.flags,
      u32(seconds),u32(hundredths),sf,u32(bonus),u32(shared)};
    std::memcpy(output,values,sizeof values);for(u32 n=0;n<8;++n)output[15+n]=u32(e.interrupts[n].health);
}
API(value) u32 value(u32 n){return output[n];}
