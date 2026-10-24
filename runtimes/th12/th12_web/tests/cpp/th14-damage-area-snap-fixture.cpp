#include "../../cpp/game/ShotDamageTh14.hpp"
#include "../../cpp/game/EclContext.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static Th14DamageArea area;
static float rate=1;
API(begin) void begin(float x,float y,float input_rate,u32 flags){
    rate=input_rate;area={};area.flags=flags;area.radius=32;area.growth=16;area.angle=.37f;
    area.position={x,y,.25f};area.timer.set(30,&rate);area.timer.previous=30;
    area.damage=150;area.total=3900;area.maximum=9999999;area.period=1;area.stamp=148;
}
API(tick) void tick(){th14_damage_tick(area);}
API(value) u32 value(u32 k){
    const u32 v[]={area.flags,float_bits(area.radius),float_bits(area.growth),float_bits(area.angle),float_bits(area.angular_velocity),float_bits(area.position.x),float_bits(area.position.y),float_bits(area.position.z),u32(area.timer.previous),u32(area.timer.current),float_bits(area.timer.fractional),u32(area.damage),u32(area.total),u32(area.maximum),u32(area.period),area.stamp};
    return k<16?v[k]:0xffffffffu;
}
