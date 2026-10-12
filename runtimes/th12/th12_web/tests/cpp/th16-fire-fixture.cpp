#include "../../cpp/game/BulletTh16.hpp"
#include "../../cpp/game/EnemyCommands.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static EnemyState enemy;static u32 values[3],events[128][3],count,limit;static i32 status;
struct Services:Th16FireServices{
 i32 spawn(const Th16BulletEmitter&,i32 index,i32 layer,float aim)override{events[count][0]=index;events[count][1]=layer;events[count++][2]=float_bits(aim);return limit&&count>=limit?1:status;}
 bool sound(i32 id,float x)override{events[count][0]=0xffffffff;events[count][1]=id;events[count++][2]=float_bits(x);return true;}
};
API(position) i32 position(u32 index,float origin_z){enemy={};enemy.current.position={11.25,37.5,2.25};enemy.th16_emitters.bases[index]={index*.25f-3,4.125,-2};enemy.th16_emitters.origins[index]={7.75,-9.5,origin_z};const bool ok=enemy_th16_fire_position(enemy,index);const auto& p=enemy.th16_emitters.records[index].position;values[0]=float_bits(p.x);values[1]=float_bits(p.y);values[2]=float_bits(p.z);return ok;}
API(value) u32 value(u32 n){return values[n];}
API(batch) i32 batch(i32 n,i32 layers,u32 flags,i32 result,u32 stop,float x,float y){Th16BulletEmitter e{};e.position={1,2,3};e.count=i16(n);e.layers=i16(layers);e.flags=flags;e.fire_sound=21;count=0;status=result;limit=stop;Services services;return bullet_th16_fire(e,{x,y,0},services);}
API(event_count) u32 event_count(){return count;}
API(event) u32 event(u32 n,u32 field){return events[n][field];}
