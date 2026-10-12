#include "../../cpp/game/ItemManager.hpp"
#include "../../cpp/game/EnemyCommands.hpp"
#include <vector>
#include <array>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static EnemyState enemy;static Rng random;
struct Services final:Th16DropServices{std::vector<std::array<u32,7>> events;bool spawn(i32 type,Vec3 p,float angle,float speed)override{events.push_back({u32(type),float_bits(p.x),float_bits(p.y),float_bits(p.z),float_bits(angle),float_bits(speed),0});return true;}} services;
API(begin) i32 begin(u32 seed){
 enemy={};random={};random.seed=u16(seed*997+17);random.calls=9;services.events.clear();auto& d=enemy.drops;
 d.primary=std::array<i32,6>{0,1,8,15,16,0}[(seed/2)%6];for(u32 n=0;n<17;++n)d.counts[n]=n==seed%16||n==15?i32((seed/12+n)%4):n==16?-1:0;
 enemy.th16_time_drop_minimum=std::array<i32,3>{0,1,3}[(seed/48)%3];enemy.th16_time_drop_duration=60;enemy.th16_time_drop_timer.current=std::array<i32,6>{-1,0,1,30,60,90}[(seed/144)%6];d.spread={std::array<float,3>{-8,0,32}[(seed/96)%3],std::array<float,3>{0,16,64}[(seed/288)%3]};
 if(seed&1)return 1;if(!enemy_th16_time_drop_decay(enemy))return 0;return item_th16_drop(d,{7.25f,300.5f,1.25f},random,services);
}
API(value) u32 value(u32 n){return n==0?random.seed:n==1?random.calls:n==2?u32(enemy.drops.primary):u32(enemy.drops.counts[n-3]);}
API(count) u32 count(){return services.events.size();}
API(event) u32 event(u32 n,u32 k){return services.events[n][k];}
