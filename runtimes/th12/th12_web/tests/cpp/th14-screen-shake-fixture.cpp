#include "../../cpp/game/EnemyManager.hpp"
#include "../../cpp/game/ScreenShake.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static Enemy owner;static EnemyEnvironment environment;static EnemyCommandEnvironment commands;static EclProgram program;
struct World:EnemyFrameWorld{void clear_shot_targets(Enemy*)override{}};static World world;
static EnemyManager manager(program,environment,commands,world);static ScreenShakes shakes;static Rng rng;static i32 result;
API(begin) i32 begin(i32 duration,i32 from,i32 to,float rate,u32 seed){
 shakes.effects.clear();shakes.offset={3,-5};rng={u16(seed),0,0};environment.rate=rate;commands.shakes=&shakes;
 alignas(4) u8 bytes[28]{};auto* ins=reinterpret_cast<EclInstruction*>(bytes);ins->opcode=517;ins->length=28;const i32 args[]={duration,from,to};std::memcpy(bytes+16,args,12);
 EclContext context;context.instruction=ins;EnemyScriptServices services(owner.state,environment,commands);return services.command(context);
}
API(initial) u32 initial(u32 n){auto& e=shakes.effects.front();const i32 values[]={e.duration,e.start,e.end,e.timer.previous,e.timer.current};if(n<5)return u32(values[n]);if(n==5){u32 v;std::memcpy(&v,&e.timer.fractional,4);return v;}return e.timer.flags;}
API(tick) void tick(u32 stopped){result=shakes.effects.front().update(rng,shakes.offset,stopped);}
API(begin_hold) i32 begin_hold(i32 amplitude,i32 ramp,i32 hold,i32 fall,float rate,u32 seed){
 shakes.effects.clear();shakes.offset={3,-5};rng={u16(seed),0,0};environment.rate=rate;shakes.start_th14_hold(amplitude,ramp,hold,fall,&environment.rate);return 0;
}
API(value) u32 value(u32 n){auto& t=shakes.effects.front().timer;if(n==0)return u32(result);if(n==1)return u32(t.previous);if(n==2)return u32(t.current);if(n==6)return rng.seed;if(n==7)return rng.calls;const float f=n==3?t.fractional:n==4?shakes.offset.x:shakes.offset.y;u32 v;std::memcpy(&v,&f,4);return v;}
