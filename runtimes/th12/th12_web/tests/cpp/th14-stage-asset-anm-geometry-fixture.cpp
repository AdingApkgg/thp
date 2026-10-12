#include "../../cpp/game/AnmManager.hpp"
#include <cstdlib>
using namespace th11;
static AnmManager manager;static AnmResource resource;static AnmVm vm;static u32 slot=0;
static u32 word(float x){u32 v;std::memcpy(&v,&x,4);return v;}
#define API(name) extern "C" __attribute__((export_name(#name)))
API(allocate) void* allocate(u32 n){return std::malloc(n);}API(release) void release(void* p){std::free(p);}
API(open) u32 open(const u8* p,u32 n,u32 file,float rate){manager.release_geometry(vm);manager.clear();resource={};manager.rate=rate;manager.script_rng={12345,0,0};manager.visual_rng={54321,0,0};return resource.open(p,n)&&manager.prepare_resource(resource,u16(file));}
API(begin) u32 begin(u32 script,u32 file){manager.release_geometry(vm);vm={};slot=script;manager.script_rng={12345,0,0};manager.visual_rng={54321,0,0};return vm.copy_script(resource,i32(script),u16(file),&manager.rate);}
API(tick) i32 tick(){return vm.update(manager);}
static std::vector<u32> fields(const AnmVm& v){std::vector<u32> out={v.sprite?u32(v.sprite_index):u32(-1),v.flags&1,v.drawing_mode(),v.color,v.secondary_color,v.layer,v.flags2,u32(v.timer.previous),u32(v.timer.current),word(v.timer.fractional),u32(v.age.previous),u32(v.age.current),word(v.age.fractional)};
 for(const float x:{v.script_position.x,v.script_position.y,v.script_position.z,v.rotation.x,v.rotation.y,v.rotation.z,v.angular_velocity.x,v.angular_velocity.y,v.angular_velocity.z,v.scale.x,v.scale.y,v.extra_scale.x,v.extra_scale.y,v.texture_scale.x,v.texture_scale.y,v.uv_offset.x,v.uv_offset.y,v.scroll_velocity.x,v.scroll_velocity.y,v.sprite_size.x,v.sprite_size.y})out.push_back(word(x));
 for(const auto& uv:v.uv){out.push_back(word(uv.x));out.push_back(word(uv.y));}for(i32 i:v.integers)out.push_back(u32(i));for(float x:v.floats)out.push_back(word(x));out.push_back(v.instruction?u32(reinterpret_cast<const u8*>(v.instruction)-reinterpret_cast<const u8*>(v.script_begin)):u32(-1));return out;}
API(count) u32 count(){return fields(vm).size();}API(field) u32 field(u32 i){return fields(vm)[i];}API(template_field) u32 template_field(u32 i){return fields(resource.templates->scripts[slot])[i];}
API(rng) u32 rng(u32 i){const u32 words[]={u32(manager.script_rng.seed)|(u32(manager.script_rng.reserved)<<16),manager.script_rng.calls,u32(manager.visual_rng.seed)|(u32(manager.visual_rng.reserved)<<16),manager.visual_rng.calls};return words[i];}

API(geometry_count) u32 geometry_count(){return vm.geometry?u32(vm.integers[0])*12u:0;}
API(geometry_field) u32 geometry_field(u32 i){u32 v;std::memcpy(&v,static_cast<u8*>(vm.geometry)+i*4,4);return v;}
