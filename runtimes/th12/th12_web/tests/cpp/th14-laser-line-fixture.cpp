#include "../../cpp/game/LaserManager.hpp"
#include "../../cpp/game/EclContext.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
namespace {
struct World:LaserWorld {
 std::vector<u32> deliveries;
 std::vector<std::vector<u32>> collisions;i32 hit=0;
 bool sound(i32,float,bool)override{return true;}
 bool cancel_effect(Vec3 p,i32 script)override{deliveries.insert(deliveries.end(),{u32(script),float_bits(p.x),float_bits(p.y),float_bits(p.z)});return true;}
 bool th14_curve_reward(Vec3 p,u32 rewards)override{if(rewards)deliveries.insert(deliveries.end(),{0x10000+rewards,float_bits(p.x),float_bits(p.y),float_bits(p.z)});return true;}
 i32 test(Vec3 p,float angle,float width,float length,u32 probe){collisions.push_back({0,float_bits(p.x),float_bits(p.y),float_bits(p.z),float_bits(angle),float_bits(width),float_bits(length),probe});return hit;}
 i32 collision(Vec3 p,float a,float w,float l)override{return test(p,a,w,l,0);}
 i32 warning_collision(Vec3 p,float a,float w,float l)override{return test(p,a,w,l,1);}
 bool th14_curve_graze(Vec3 p)override{collisions.push_back({1,float_bits(p.x),float_bits(p.y),float_bits(p.z)});return true;}
 i32 th14_line_cut(Th14LaserLine&,Vec3 p,Vec2 s,float angle,u32 rewards,bool skip)override{collisions.push_back({2,float_bits(p.x),float_bits(p.y),float_bits(p.z),float_bits(s.x),float_bits(s.y),float_bits(angle),rewards,u32(skip)});return 0;}
} world;
Th14LaserLine laser;
std::vector<std::array<u8,0x354>> fragments;
std::vector<std::vector<u32>> factory_results;std::vector<u32> registry_parent;
}
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(initialize) void initialize(const u8* request,float rate){laser=Th14LaserLine{};world.rate=rate;laser.base.initialize(&world.rate);laser_th14_line_initialize_state(laser,request,world);laser.body.flags=0x10;}
API(tick) i32 tick(){const auto result=laser_th14_line_step(laser,world);if(!result)laser.base.lifetime.tick();return result;}
API(value) u32 value(u32 n){const auto& b=laser.base;u32 limit;std::memcpy(&limit,laser.request+0x10,4);const u32 values[]={u32(b.state),u32(b.type),float_bits(b.position.x),float_bits(b.position.y),float_bits(b.position.z),float_bits(b.velocity.x),float_bits(b.velocity.y),float_bits(b.velocity.z),float_bits(b.angle),float_bits(b.length),float_bits(b.width),float_bits(b.speed),float_bits(b.offset),u32(b.transform_index),b.active_transforms,u32(b.protection),u32(b.offscreen_timer.previous),u32(b.offscreen_timer.current),float_bits(b.offscreen_timer.fractional),u32(b.graze_timer.previous),u32(b.graze_timer.current),float_bits(b.graze_timer.fractional),u32(laser.motion_clock.previous),u32(laser.motion_clock.current),float_bits(laser.motion_clock.fractional),u32(b.lifetime.previous),u32(b.lifetime.current),float_bits(b.lifetime.fractional),limit,u32(b.id),(laser.body.flags&0x70u)<<1};return values[n];}
API(cancel) i32 cancel(i32 sprite,u32 length,u32 angle,u32 mode){laser=Th14LaserLine{};auto& b=laser.base;b.sprite=i16(sprite);b.color=7;b.angle=float_bits(angle);b.length=float_bits(length);b.position={-180.25f,7.5f,3.25f};b.state=2;b.protection=mode==2?3:0;world.deliveries.clear();return laser_th14_line_cancel(laser,mode!=0,mode==2,world);}
API(delivery_count) u32 delivery_count(){return world.deliveries.size()/4;}
API(delivery_word) u32 delivery_word(u32 n){return world.deliveries.at(n);}
API(circle) i32 circle(const u8* request,u32 radius,u32 mode){initialize(request,1);laser.base.protection=mode==2?3:0;world.deliveries.clear();return laser_th14_line_cut_circle(laser,{-140.25f,7.5f,0},float_bits(radius),mode==1?1u:0u,mode==2,fragments,world);}
API(rectangle) i32 rectangle(const u8* request,u32 width,u32 height,u32 angle,u32 mode){initialize(request,1);laser.base.protection=mode==2?3:0;world.deliveries.clear();return laser_th14_line_cut_rectangle(laser,{-140.25f,7.5f,0},{float_bits(width),float_bits(height)},float_bits(angle),mode==1?1u:0u,mode==2,fragments,world);}
API(circle_value) u32 circle_value(u32 n){const auto& b=laser.base;u32 limit;std::memcpy(&limit,laser.request+0x10,4);const u32 values[]={laser.native_flags,float_bits(b.position.x),float_bits(b.position.y),float_bits(b.position.z),float_bits(b.length),float_bits(b.offset),limit};return values[n];}
API(fragment_count) u32 fragment_count(){return fragments.size();}
API(fragment_word) u32 fragment_word(u32 n,u32 j){u32 v;std::memcpy(&v,fragments.at(n).data()+4*j,4);return v;}
API(collision) i32 collision(u32 length,u32 width,u32 angle,float rate,u32 age,i32 hit,u32 probe){laser=Th14LaserLine{};world.rate=rate;world.player={17.25f,120.5f,3.25f};world.hit=hit;world.collisions.clear();auto& b=laser.base;b.position={-22.25f,40.5f,3.25f};b.length=float_bits(length);b.width=float_bits(width);b.angle=float_bits(angle);b.graze_timer.set(i32(age),&world.rate);return laser_th14_line_collision(laser,world,probe);}
API(collision_count) u32 collision_count(){return world.collisions.size();}
API(collision_size) u32 collision_size(u32 n){return world.collisions.at(n).size();}
API(collision_word) u32 collision_word(u32 n,u32 k){return world.collisions.at(n).at(k);}
API(registry) i32 registry(const u8* request,u32 radius,u32 width,u32 height,u32 angle,u32 mode,u32 rectangle){
 world.rate=1;world.deliveries.clear();factory_results.clear();AnmResource resource;AnmEnvironment animations;
 resource.scripts.resize(300);for(auto& s:resource.scripts)s.bytes={2,0,8,0,0,0,0,0,255,255,0,0,0,0,0,0};
 LaserManager manager(resource,animations,world,6);auto* parent=new Th14LaserLine{};parent->base.initialize(&manager.rate);laser_th14_line_initialize_state(*parent,request,manager);parent->base.protection=mode==2?3:0;parent->base.rectangle_enabled=1;manager.append(parent->base);
 const i32 count=rectangle?manager.th14_line_cut(*parent,{-140.25f,7.5f,0},{float_bits(width),float_bits(height)},float_bits(angle),mode==1?1u:0u,mode==2):manager.cancel_circle({-140.25f,7.5f,0},float_bits(radius),mode==1?1u:0u,mode==2);
 const auto& b=parent->base;u32 limit;std::memcpy(&limit,parent->request+0x10,4);registry_parent={parent->native_flags,float_bits(b.position.x),float_bits(b.position.y),float_bits(b.position.z),float_bits(b.length),float_bits(b.offset),limit,manager.active_count,u32(manager.last_error)};
 for(auto* node=b.next;node;node=node->next){const auto& child=*reinterpret_cast<Th14LaserLine*>(node);std::vector<u32> values(213);std::memcpy(values.data(),child.request,0x354);laser=child;for(u32 j=0;j<31;++j)values.push_back(value(j));factory_results.push_back(values);}
 return count;
}
API(registry_value) u32 registry_value(u32 n){return registry_parent.at(n);}
API(factory_count) u32 factory_count(){return factory_results.size();}
API(factory_word) u32 factory_word(u32 n,u32 k){return factory_results.at(n).at(k);}
API(scale_case) i32 scale_case(float length,float width,float sw,float sh,float rate){
 laser=Th14LaserLine{};world.rate=rate;world.hit=0;AnmEnvironment animations;animations.rate=rate;static AnmSprite sprite;sprite.width=sw;sprite.height=sh;auto& b=laser.base;b.initialize(&world.rate);b.state=2;b.position={-22.25f,40.5f,3.25f};b.length=length;b.width=width;b.offscreen_timer.set(30,&world.rate);std::memcpy(laser.request+0x10,&length,4);laser.motion_clock.set(0,&world.rate);laser.body.sprite=&sprite;return laser_th14_line_update(laser,animations,world);
}
API(scale_value) u32 scale_value(u32 n){const u32 values[]={float_bits(laser.body.scale.x),float_bits(laser.body.scale.y),u32(laser.motion_clock.previous),u32(laser.motion_clock.current),float_bits(laser.motion_clock.fractional)};return values[n];}
