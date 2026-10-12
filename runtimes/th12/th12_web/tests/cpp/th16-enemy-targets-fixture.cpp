#include "../../cpp/game/EnemyTh16Targets.hpp"
#include "../../cpp/game/EnemyState.hpp"
#include "../../cpp/game/EclContext.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static Enemy enemies[8];static EnemyLink nodes[8];static u32 result[3];
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(run_case) void run_case(u32 count,const u32* values,float x,float y,float z,float radius,u32 id){
 for(u32 i=0;i<count;i++){auto& state=enemies[i].state;const auto* v=values+i*5;state.instance_id=i32(v[0]);state.flags=v[1];state.current.position={float_bits(v[2]),float_bits(v[3]),float_bits(v[4])};nodes[i]={&enemies[i],i+1<count?&nodes[i+1]:nullptr,i?&nodes[i-1]:nullptr};}
 auto* list=count?nodes:nullptr;result[0]=enemy_th16_nearest(list,{x,y,z},radius);result[1]=enemy_th16_valid(list,id);auto* found=enemy_th16_lookup(list,id);result[2]=found?u32(found-enemies):0xffffffff;
}
API(value) u32 value(u32 n){return result[n];}
