#include "ShotManager.hpp"
#include <array>
using namespace th11;
namespace {
struct World:Th14DamageWorld {
    NativeStackTh14 stack;
    Rng rng;
    Vec3 position;
    float rotation=0;
    bool use_stack=true;
    bool hit(u32,Th14DamageArea& a,const Vec3& p,const Vec2*,float,float,i32& result)override{
        shot_th14_reimu_bomb_hit(a,p,rng,position,rotation,use_stack?stack.damage_polar_z():0);
        stack.damage_polar_store(position.z);result=a.damage;return true;
    }
};
u32 result[9]{};
u32 word(float value){u32 out;std::memcpy(&out,&value,4);return out;}
}
extern "C" __attribute__((export_name("run"))) u32 run(u32 circle,u32 rectangle,float delta,u32 seed,u32 poison,u32 use_stack){
    std::array<Th14DamageArea,256> pool{};auto& a=pool[0];a.flags=circle?7:5;
    a.radius=64;a.angle=.5f;a.size={96,64};a.position={17,123,0};
    a.timer.previous=2;a.timer.current=3;a.timer.fractional=3;a.damage=19;a.maximum=9999999;a.period=1;a.callback=2;
    World world;world.stack.damage_scratch=poison;world.rng.seed=u16(seed);world.rng.calls=0;world.use_stack=use_stack;
    GameEconomy economy;bool bomb=false;i32 damage=0;Vec2 size{48,32};
    if(!th14_damage_collect(pool,world,{17+delta,123+delta,0},rectangle?&size:nullptr,8,-.25f,true,false,0,0,220,economy,damage,bomb,nullptr,&world.stack))return 0;
    const u32 values[]={u32(damage),u32(bomb),word(world.position.x),word(world.position.y),word(world.position.z),word(world.rotation),world.rng.seed,world.rng.calls,world.stack.damage_scratch};
    for(u32 i=0;i<9;++i)result[i]=values[i];return 1;
}
extern "C" __attribute__((export_name("value"))) u32 value(u32 n){return n<9?result[n]:0xffffffffu;}
