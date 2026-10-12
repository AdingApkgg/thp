#include "../../cpp/game/ShotDamageTh14.hpp"
using namespace th11;
static u32 float_bits(float x){u32 v;std::memcpy(&v,&x,4);return v;}
#define API(name) extern "C" __attribute__((export_name(#name)))
static std::array<Th14DamageArea,256> pool;static u32 cursor,selected;static float rate;
API(begin) i32 begin(u32 start,u32 occupied,i32 duration,float speed,u32 variant){
 const float values[][4]={{32,16,0,0},{-2,.25f,3.1f,.1f},{0,-1,-3.1f,-.1f},{5,0,8,0}};cursor=start;rate=speed;
 for(auto& a:pool){a={};a.flags=0x8006;a.angle=values[variant][2];a.angular_velocity=values[variant][3];a.size={17,19};a.total=77;a.stamp=66;a.callback=55;}
 for(u32 n=0;n<occupied;++n)pool[(start%256+n)%256].flags=0x8007;
 return th14_damage_circle(pool,cursor,{-12.5f,400,2},values[variant][0],values[variant][1],duration,150,&rate,selected)?0:-1;
}
API(tick) void tick(){for(auto& a:pool)th14_damage_tick(a);}
API(begin_rectangle) i32 begin_rectangle(u32 start,u32 occupied,i32 duration,float speed,u32 variant){
 const float values[][4]={{32,16,0,0},{-2,.25f,3.1f,.1f},{0,-1,-3.1f,-.1f},{5,0,8,0}};cursor=start;rate=speed;
 for(auto& a:pool){a={};a.flags=0x8006;a.angle=values[variant][2];a.angular_velocity=values[variant][3];a.size={17,19};a.total=77;a.stamp=66;a.callback=55;}
 for(u32 n=0;n<occupied;++n)pool[(start%256+n)%256].flags=0x8007;
 return th14_damage_rectangle(pool,cursor,{-12.5f,400,2},{values[variant][0],values[variant][1]},values[variant][2],duration,150,&rate,selected)?0:-1;
}
API(meta) u32 meta(u32 n){return n?cursor:selected;}
API(word) u32 word(u32 n){const auto& a=pool[selected];const u32 v[]={a.flags,float_bits(a.radius),float_bits(a.growth),float_bits(a.angle),float_bits(a.angular_velocity),float_bits(a.size.x),float_bits(a.size.y),float_bits(a.position.x),float_bits(a.position.y),float_bits(a.position.z),u32(a.timer.previous),u32(a.timer.current),float_bits(a.timer.fractional),u32(a.damage),u32(a.total),u32(a.maximum),u32(a.period),a.stamp,a.callback};return v[n];}
