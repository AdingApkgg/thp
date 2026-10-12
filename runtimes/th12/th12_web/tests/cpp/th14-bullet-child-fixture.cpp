#include "../../cpp/game/BulletState.hpp"
#include "../../cpp/game/BulletTh14.hpp"
#include "../../cpp/game/BulletManager.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
namespace {
struct World:BulletEnvironment{std::vector<Th14BulletEmitter> requests;u32 cancels=0;bool fire_th14(const Th14BulletEmitter& e)override{requests.push_back(e);return true;}bool cancel(BulletState&)override{++cancels;return true;}} world;
BulletState bullet;
std::vector<u32> pool_results;
}
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(run) i32 run(const u8* program,i32 index,u32 active){bullet={};world.requests.clear();world.cancels=0;bullet.position={12.25f,80.5f,3.25f};bullet.speed=2.75f;bullet.angle=-.125f;bullet.transform_index=index;bullet.active_transforms=active;std::memcpy(bullet.th14_transforms,program,0x318);return bullet_th14_start_transforms(bullet,world);}
API(value) u32 value(u32 n){const u32 values[]={u32(bullet.transform_index),bullet.active_transforms,world.cancels};return values[n];}
API(request_count) u32 request_count(){return world.requests.size();}
API(request_word) u32 request_word(u32 n,u32 k){u32 v;std::memcpy(&v,reinterpret_cast<const u8*>(&world.requests.at(n))+k*4,4);return v;}
API(pool) i32 pool(i32 count,i32 layers,float angle,float speed,u32 cancel,float rate,u32 filled){
 struct PoolWorld:BulletWorld{bool sound(i32,float,bool)override{return true;}bool effect(const Vec3&,i32)override{return true;}i32 collision(const BulletState&)override{return 0;}} pw;
 AnmResource resource;AnmEnvironment animations;animations.rate=rate;resource.scripts.resize(300);for(auto& s:resource.scripts)s.bytes={2,0,8,0,0,0,0,0,255,255,0,0,0,0,0,0};
 BulletManager manager(resource,animations,pw,6);Th14BulletEmitter emitter{};emitter.count=emitter.layers=emitter.aim=1;emitter.position={12.25f,80.5f,3.25f};emitter.angle=-.125f;emitter.speed=2.75f;emitter.transform_sound=-1;
 for(u32 j=0;j<filled;++j)if(manager.spawn_th14(emitter,0,0,0))return -2;
 if(manager.spawn_th14(emitter,0,0,0))return -2;auto& parent=*manager.first_th14();const Vec3 position=parent.position,velocity=parent.velocity;
 auto& t=parent.th14_transforms[0];t={};t.opcode=0x2000;t.a=angle;t.b=.35f;t.c=speed;t.d=.75f;t.p=1;t.q=2;t.r=count;t.s=layers;auto& next=parent.th14_transforms[1];next={};next.p=0;next.q=3;next.r=i32(cancel);
 const i32 result=bullet_th14_start_transforms(parent,manager);u32 children=0,bad=0,total=0;
 for(auto* p=manager.first_th14();p;p=p->th14_active_next){++total;if(p!=&parent&&p->color==3){++children;if(p->sprite!=0||p->state!=1||p->transform_index!=2||p->active_transforms||p->lifetime.current)++bad;}}
 const Vec3 expected=cancel?Vec3{position.x+(velocity.x*rate)*.5f,position.y+(velocity.y*rate)*.5f,position.z+(velocity.z*rate)*.5f}:position;
 pool_results={total,children,bad,u32(parent.state),u32(parent.transform_index),u32(manager.last_error),u32(parent.position.x==expected.x&&parent.position.y==expected.y&&parent.position.z==expected.z)};return result;
}
API(pool_value) u32 pool_value(u32 n){return pool_results.at(n);}
