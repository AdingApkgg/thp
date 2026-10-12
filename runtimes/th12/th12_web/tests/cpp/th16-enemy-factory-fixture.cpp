#include "../../cpp/game/EnemyManager.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static EnemyState e;static float rate=1;
API(run_case) void run_case(u32 flags,u32 mirror,u32 world,i32 health,i32 file,i32 script,i32 death){
 e={};e.flags=flags;e.instance_id=22;e.bound_animation_file=file;e.animation_script=script;e.death_animation=death;e.death_animation_file=6;
 EnemySpawn p;p.position={1,-2,3};p.score=1007;p.health=health;p.drop=4;p.mirrored=mirror;p.world_coordinates=world;p.parent_instance_id=123;
 u32 inherited[12];for(u32 j=0;j<12;++j)inherited[j]=0x12340000+j;std::memcpy(p.integers,inherited,48);
 enemy_th16_bind_spawn(e,p,&rate,9);enemy_th16_death_metadata(e);
}
API(value) u32 value(u32 n){
 const u32 data[]={float_bits(e.absolute.position.x),float_bits(e.absolute.position.y),float_bits(e.absolute.position.z),u32(e.score),u32(e.health),u32(e.max_health),u32(e.drops.primary),e.flags,e.parent_instance_id,u32(e.drops.counts[15]),u32(e.th16_time_drop_timer.previous),u32(e.th16_time_drop_timer.current),float_bits(e.th16_time_drop_timer.fractional),u32(e.th16_time_drop_duration),u32(e.th16_time_drop_minimum),u32(e.th16_chapter_tag),u32(e.death_sound),u32(e.death_animation),u32(e.death_animation_file)};
 if(n<19)return data[n];u32 v;std::memcpy(&v,reinterpret_cast<const u8*>(e.integers)+(n-19)*4,4);return v;
}
