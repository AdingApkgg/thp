#include "../../cpp/game/ShotTh16.hpp"
#include "../../cpp/game/ShotManager.hpp"
#include <vector>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static Th16ShotSpawn shot;static Th16DamageSources sources;static Rng random;static std::array<u32,16> lasers;static float rate;
struct Delivery final:Th16ShotDelivery {
 u32 flags=0x100,flags2=0;float rotation=3.25f;Vec3 world{11,22,33};std::vector<std::array<u32,4>> events;
 u32 create(bool season,i32 script)override{events.push_back({1,u32(season),u32(script),0xffffffff});return 77;}
 bool orient(u32,float angle)override{if(flags2&0x80){flags|=4;rotation=angle;}return true;}
 bool position(u32,Vec3 p)override{world=p;return true;}
 void erase(u32 id)override{events.push_back({4,id,0,0});}
 i32 callback(Th16ShotSpawn& s,const ShotSpec& spec,i32 frame)override{if(u32(spec.spawn)==1)events.push_back({2,1,u32(frame),0});if(u32(spec.spawn)==7){events.push_back({2,7,u32(frame),0});return 1;}if(u32(spec.spawn)==2)sound(20,7.25f);return shot_th16_spawn_callback(s,spec,sources)?0:-1;}
 bool sound(i32 sound,float x)override{events.push_back({3,u32(sound),float_bits(x),0});return true;}
} delivery;
API(begin) i32 begin(i32 number,i32 kind,float angle,u32 focus,u32 family,u32 callback,u32 flags2,i32 cursor,i32 sound){
 shot={};shot.flags=0x80000000;shot.target_id=123;shot.timer.flags=1;rate=.5f;shot.timer.rate=&rate;random={12345,0,17};lasers.fill(123);
 sources={};sources.cursor=cursor;for(auto& r:sources.records){for(u32 i=0;i<37;++i)r.words[i]=0xa5000000+i;r.words[0]=0xabcdef06;}
 delivery=Delivery{};delivery.flags2=flags2;
 ShotSpec spec;spec.option=i8(number);spec.type=i8(kind);spec.damage=13;spec.hitbox={4.25,7.5};spec.offset={2.25,-3.5};spec.angle=angle;spec.speed=6.25f;spec.animation=7;spec.hit_animation=i16(sound);spec.spawn=ShotSpawn(callback);
 ShotPlayer player;player.power=399;player.power_step=100;player.focused=focus;for(i32 i=0;i<12;++i)player.options[i]={-321+i*777,50319-i*333,(i-5)*.75f,0};
 return shot_th16_spawn(shot,spec,family?0x10000:0,19,7,player,{7.25,400.5,1.25},random,lasers,sources,&rate,delivery);
}
API(value) u32 value(u32 n){const u32 words[]={shot.flags,u32(shot.state),shot.packed,u32(shot.timer.previous),u32(shot.timer.current),float_bits(shot.timer.fractional),u32(shot.damage),float_bits(shot.hitbox.x),float_bits(shot.hitbox.y),random.seed,random.calls,shot.animation,shot.damage_source,shot.target_id,u32(sources.cursor),delivery.flags,delivery.flags2,float_bits(delivery.rotation),float_bits(delivery.world.x),float_bits(delivery.world.y),float_bits(delivery.world.z)};return n<21?words[n]:lasers[n-21];}
API(movement) u32 movement(u32 n){const auto& m=shot.movement;const float words[]={m.position.x,m.position.y,m.position.z,m.speed,m.angle,m.velocity.x,m.velocity.y,m.velocity.z};return float_bits(words[n]);}
API(area) u32 area(u32 n){return sources.records[shot.damage_source].words[n];}
API(count) u32 count(){return delivery.events.size();}
API(event) u32 event(u32 n,u32 k){return delivery.events[n][k];}
