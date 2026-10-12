#include "../../cpp/game/LaserManager.hpp"
#include "../../cpp/game/EclContext.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
namespace{
struct World:LaserWorld{std::vector<std::array<u8,0x354>> requests;u32 sounds=0;bool sound(i32,float,bool)override{++sounds;return false;}bool th14_line_spawn(const u8* p)override{std::array<u8,0x354> r;std::memcpy(r.data(),p,r.size());requests.push_back(r);return true;}}world;
Th14LaserLine laser,saved;
std::vector<std::array<u32,9>> children;
u32 registry_count=0; i32 registry_error=0;
}
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(initialize) i32 initialize(const u8* p,float rate){world.rate=rate;world.requests.clear();world.sounds=0;laser={};laser.base.initialize(&world.rate);laser_th14_line_initialize_state(laser,p,world);const auto result=laser_th14_line_transforms(laser,world);saved=laser;return result;}
API(tick) i32 tick(){return laser.base.active_transforms&0x40?laser_th14_line_bounce(laser,world):0;}
API(full_tick) i32 full_tick(){laser=saved;world.requests.clear();world.sounds=0;return laser_th14_line_step(laser,world);}
API(value) u32 value(u32 n){const auto& b=laser.base;const auto& s=b.motion[4];const u32 v[]={u32(b.transform_index),b.active_transforms,u32(b.protection),float_bits(s.a),u32(s.limit),u32(s.count),u32(s.duration),float_bits(b.position.x),float_bits(b.position.y),float_bits(b.position.z),float_bits(b.angle),float_bits(b.length),float_bits(b.speed),float_bits(b.offset),u32(b.offscreen_timer.previous),u32(b.offscreen_timer.current),float_bits(b.offscreen_timer.fractional)};if(n<17)return v[n];if(n<230){u32 word;std::memcpy(&word,laser.request+(n-17)*4,4);return word;}return world.sounds;}
API(request_count) u32 request_count(){return world.requests.size();}
API(request_word) u32 request_word(u32 n,u32 k){u32 word;std::memcpy(&word,world.requests.at(n).data()+4*k,4);return word;}
API(registry) i32 registry(const u8* request,float rate){
 world.rate=rate;world.requests.clear();world.sounds=0;children.clear();AnmResource resource;AnmEnvironment animations;animations.rate=rate;
 resource.scripts.resize(300);for(auto& s:resource.scripts)s.bytes={2,0,8,0,0,0,0,0,255,255,0,0,0,0,0,0};
 LaserManager manager(resource,animations,world,6);auto* parent=new Th14LaserLine{};parent->base.initialize(&manager.rate);laser_th14_line_initialize_state(*parent,request,manager);manager.append(parent->base);
 if(laser_th14_line_transforms(*parent,manager)<0)return -2;const i32 result=laser_th14_line_step(*parent,manager);laser=*parent;
 for(auto* p=parent->base.next;p;p=p->next){const auto& child=*reinterpret_cast<Th14LaserLine*>(p);std::array<u8,0x354> r;std::memcpy(r.data(),child.request,r.size());world.requests.push_back(r);children.push_back({float_bits(p->position.x),float_bits(p->position.y),float_bits(p->position.z),float_bits(p->angle),float_bits(p->speed),float_bits(p->length),float_bits(p->width),u32(p->transform_index),p->active_transforms});}
 registry_count=manager.active_count;registry_error=manager.last_error;return result;
}
API(registry_value) u32 registry_value(u32 n){return n?u32(registry_error):registry_count;}
API(child_value) u32 child_value(u32 n,u32 k){return children.at(n).at(k);}
