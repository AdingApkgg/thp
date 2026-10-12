#include "../../cpp/game/BulletTh16.hpp"
#include "../../cpp/game/EclContext.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static BulletState b;static float rate=1;static Th16BulletEmitter requests[32];static u32 count,events[64][2],event_count_;static const Vec3 player{-15.5f,400,0};
struct Services:Th16BulletStepServices{
 i32 collision(BulletState&)override{return -2;}i32 animation(AnmVm&)override{return -2;}
 bool fire(const Th16BulletEmitter& e)override{requests[count++]=e;events[event_count_][0]=0;events[event_count_++][1]=b.transform_index;return true;}
 bool cancel(BulletState&)override{events[event_count_][0]=1;events[event_count_++][1]=b.transform_index;return true;}
};
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(run) i32 run(i32 index,u32 active,i32 counter,u32 angle,const void* program){
 b={};b.position={7.125f,9.25f,.1f};b.speed=2.25f;b.angle=float_bits(angle);b.transform_index=index;b.active_transforms=active;b.reserved_4c0=counter;b.extra=7;b.transform_sound=-1;std::memcpy(b.th16_transforms,program,sizeof b.th16_transforms);count=event_count_=0;Services services;return bullet_th16_start_transforms(b,&rate,nullptr,nullptr,&player,&services);
}
API(value) u32 value(u32 n){return n==0?u32(b.transform_index):n==1?u32(b.reserved_4c0):n==2?b.active_transforms:u32(b.extra);}
API(request_count) u32 request_count(){return count;}
API(request_address) const void* request_address(u32 n){return &requests[n];}
API(event_count) u32 event_count(){return event_count_;}
API(event) u32 event(u32 n,u32 f){return events[n][f];}
