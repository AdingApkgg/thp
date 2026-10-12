#include "../../cpp/game/ShotTh16.hpp"
#include "../../cpp/game/EclContext.hpp"
#include <vector>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static Th16ShotSpawn shot;static Th16DamageSources sources;static float rate;
struct Delivery final:Th16ShotUpdateDelivery {
 u32 flags=0x100,flags2=0,missing=0,geometry=0;float rotation=3.25f;Vec3 world{11,22,33};std::vector<std::array<u32,4>> events;
 i32 update_callback(Th16ShotSpawn& s,const ShotSpec& spec)override{if(u32(spec.update)==7){events.push_back({1,7,0,0});return 1;}if(u32(spec.update)==5){events.push_back({1,5,0,0});if(s.state==1)s.movement.speed+=.5f;}return 0;}
 bool find(u32 id,u32& out)override{events.push_back({2,id,0,0});out=flags2;return !missing;}
 bool quad(u32 id,std::array<Vec3,4>& corners)override{events.push_back({3,id,0,0});for(auto& p:corners)p=geometry==0?Vec3{100,100,0}:Vec3{0,0,0};if(geometry==2)corners[2]={100,100,0};if(geometry==3){corners[0]={32,16,0};corners[1]={416,464,0};}return true;}
 void erase(u32 id)override{events.push_back({4,id,0,0});}
 void position(u32,Vec3 p)override{world=p;}
 void orient(u32,float angle)override{flags|=4;rotation=angle;}
} delivery;
API(begin) i32 begin(i32 state,i32 age,i32 type,u32 callback,u32 flags,u32 flags2,u32 missing,u32 geometry,float angle,float speed,float scale){
 shot={};shot.state=state;shot.flags=flags;shot.packed=0;shot.animation=77;shot.damage_source=2;shot.timer.flags=1;shot.timer.previous=-5;shot.timer.current=age;shot.timer.fractional=float(age)+.25f;rate=scale;shot.timer.rate=&rate;
 shot.movement.position={7.25,300.5,1.25};shot.movement.velocity={11,22,2};shot.movement.speed=speed;shot.movement.angle=angle;shot.hitbox={4.25,7.5};shot.damage=13;
 sources={};for(auto& r:sources.records)for(u32 i=0;i<37;++i)r.words[i]=0xa5000000+i;sources.records[2].words[0]=0xabcdef07;
 delivery=Delivery{};delivery.flags2=flags2;delivery.missing=missing;delivery.geometry=geometry;delivery.play_origin={32,16};
 ShotSpec spec;spec.type=i8(type);spec.update=ShotUpdate(callback);return shot_th16_update(shot,spec,sources,&rate,delivery);
}
API(value) u32 value(u32 n){const u32 words[]={shot.flags,u32(shot.state),u32(shot.timer.previous),u32(shot.timer.current),float_bits(shot.timer.fractional),shot.animation,shot.damage_source,delivery.flags,delivery.flags2,float_bits(delivery.rotation),float_bits(delivery.world.x),float_bits(delivery.world.y),float_bits(delivery.world.z)};return words[n];}
API(movement) u32 movement(u32 n){const auto& m=shot.movement;const float words[]={m.position.x,m.position.y,m.position.z,m.speed,m.angle,m.velocity.x,m.velocity.y,m.velocity.z};return float_bits(words[n]);}
API(area) u32 area(u32 n){return sources.records[2].words[n];}
API(count) u32 count(){return delivery.events.size();}
API(event) u32 event(u32 n,u32 k){return delivery.events[n][k];}
