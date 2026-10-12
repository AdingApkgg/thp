#include "../../cpp/game/ShotDamageTh14.hpp"
#include "../../cpp/game/EclContext.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
namespace {
std::array<Th14DamageArea,256> areas;GameEconomy economy;Vec3 last;bool bomb;u32 mask=0; i32 damage;float rate=1;
struct World:Th14DamageWorld{bool hit(u32 j,Th14DamageArea& a,const Vec3&,const Vec2*,float,float,i32& out)override{mask+=1u<<j;out=wrapping_add(a.damage,-i32(j)-1);return true;}}world;
}
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(run) u32 run(const u32* p){
    areas={};economy={};economy.score_units=i32(p[6]);last={111,222,333};bomb=true;mask=0;damage=0;
    for(u32 j=0;j<3;++j){const auto* v=p+14+j*18;auto& a=areas[j];a.flags=v[0];a.radius=float_bits(v[1]);a.angle=float_bits(v[2]);a.size={float_bits(v[3]),float_bits(v[4])};a.position={float_bits(v[5]),float_bits(v[6]),float_bits(v[7])};a.timer.set(i32(v[9]),&rate);a.timer.previous=i32(v[8]);a.timer.fractional=float_bits(v[10]);a.damage=i32(v[11]);a.total=i32(v[12]);a.maximum=i32(v[13]);a.period=i32(v[14]);a.stamp=v[15];a.callback=v[16];a.argument=v[17];}
    const Vec3 pos{float_bits(p[7]),float_bits(p[8]),float_bits(p[9])};const Vec2 size{float_bits(p[10]),float_bits(p[11])};
    return th14_damage_collect(areas,world,pos,p[5]?&size:nullptr,float_bits(p[12]),float_bits(p[13]),p[0],p[1],p[2],p[3],i32(p[4]),economy,damage,bomb,&last);
}
API(value) u32 value(u32 n){const u32 header[]={u32(damage),bomb?1u:0u,float_bits(last.x),float_bits(last.y),float_bits(last.z),u32(economy.score_units),mask};if(n<7)return header[n];const auto& a=areas[(n-7)/5];const u32 values[]={a.flags,u32(a.total),u32(a.damage),a.stamp,a.argument};return values[(n-7)%5];}
