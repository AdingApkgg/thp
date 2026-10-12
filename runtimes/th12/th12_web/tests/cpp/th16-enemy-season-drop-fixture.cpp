#include "../../cpp/game/EnemyCommands.hpp"
#include <vector>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static EnemyState enemy;static Rng rng;
struct Services final:Th16EnemyItemServices {
    std::vector<u32> events;
    bool spawn(Vec3 p,float angle,float speed)override{events.insert(events.end(),{16,float_bits(p.x),float_bits(p.y),float_bits(p.z),float_bits(angle),float_bits(speed),0});return true;}
} services;
API(run_case) i32 run_case(i32 step,i32 next,i32 total,u32 seed,u32 calls,float x,float y,float z){enemy.th16_damage_drop_step=step;enemy.th16_damage_drop_next=next;enemy.th16_damage_total=total;enemy.current.position={x,y,z};rng={};rng.seed=u16(seed);rng.calls=calls;services.events.clear();return enemy_th16_damage_drop(enemy,rng,services);}
API(value) u32 value(u32 n){return n==0?u32(enemy.th16_damage_drop_next):n==1?rng.seed:rng.calls;}
API(event_count) u32 event_count(){return services.events.size();}
API(event) u32 event(u32 n){return services.events[n];}
