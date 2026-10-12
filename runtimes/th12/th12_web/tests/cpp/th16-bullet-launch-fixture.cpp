#include "../../cpp/game/BulletLaunch.hpp"
#include "../../cpp/game/EnemyTh16Emitter.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static BulletLaunch launch;static Rng rng;
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(run) i32 run(i32 mode,i32 count,i32 layers,i32 index,i32 layer,u32 seed,const float* v){
    Th16BulletEmitter e{};e.aim=i16(mode);e.count=i16(count);e.layers=i16(layers);e.position={v[0],v[1],v[2]};e.angle=v[3];e.spread=v[4];e.speed=v[5];e.slow_speed=v[6];e.radius=v[7];
    rng={u16(seed),0,0};launch={};return bullet_th16_launch(e,index,layer,v[8],rng,{v[9],v[10],v[11]},v[12],launch);
}
API(value) u32 value(u32 n){if(n==7)return rng.seed;if(n==8)return rng.calls;u32 v;std::memcpy(&v,reinterpret_cast<const u8*>(&launch)+n*4,4);return v;}
