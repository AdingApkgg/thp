#include "../../cpp/game/AnmManager.hpp"
#include <cstdlib>
using namespace th11;
static AnmManager manager;static AnmResource resource;static AnmVm vm;static u32 slot=0;
static u32 word(float x){u32 v;std::memcpy(&v,&x,4);return v;}
#define API(name) extern "C" __attribute__((export_name(#name)))
API(allocate) void* allocate(u32 n){return std::malloc(n);}API(release) void release(void* p){std::free(p);}
API(open) u32 open(const u8* p,u32 n,u32 file,float rate){manager.release_geometry(vm);manager.clear();resource={};manager.rate=rate;manager.script_rng={12345,0,0};manager.visual_rng={54321,0,0};return resource.open(p,n)&&manager.prepare_resource(resource,u16(file));}
static AnmResource fallback;
API(fallback_open) u32 fallback_open(const u8* p,u32 n){const bool ok=fallback.open(p,n);if(ok)manager.fallback_sprites=&fallback;return ok;}
API(begin) u32 begin(u32 script,u32 file){manager.release_geometry(vm);vm={};slot=script;manager.script_rng={12345,0,0};manager.visual_rng={54321,0,0};return vm.copy_script(resource,i32(script),u16(file),&manager.rate);}
API(tick) i32 tick(){return vm.update(manager);}
static std::vector<u32> fields(const AnmVm& v){std::vector<u32> out={v.sprite?u32(v.sprite_index):u32(-1),v.flags&1,v.drawing_mode(),v.color,v.secondary_color,v.layer,v.flags2,u32(v.timer.previous),u32(v.timer.current),word(v.timer.fractional),u32(v.age.previous),u32(v.age.current),word(v.age.fractional)};
 for(const float x:{v.script_position.x,v.script_position.y,v.script_position.z,v.rotation.x,v.rotation.y,v.rotation.z,v.angular_velocity.x,v.angular_velocity.y,v.angular_velocity.z,v.scale.x,v.scale.y,v.extra_scale.x,v.extra_scale.y,v.texture_scale.x,v.texture_scale.y,v.uv_offset.x,v.uv_offset.y,v.scroll_velocity.x,v.scroll_velocity.y,v.sprite_size.x,v.sprite_size.y})out.push_back(word(x));
 for(const auto& uv:v.uv){out.push_back(word(uv.x));out.push_back(word(uv.y));}for(i32 i:v.integers)out.push_back(u32(i));for(float x:v.floats)out.push_back(word(x));out.push_back(v.instruction?u32(reinterpret_cast<const u8*>(v.instruction)-reinterpret_cast<const u8*>(v.script_begin)):u32(-1));return out;}
API(resource_error) u32 resource_error(){return resource.last_error;}
API(manager_error) u32 manager_error(){return manager.last_error;}
API(manager_error_offset) u32 manager_error_offset(){return manager.last_error_offset;}
API(count) u32 count(){return fields(vm).size();}API(field) u32 field(u32 i){return fields(vm)[i];}API(template_field) u32 template_field(u32 i){return fields(resource.templates->scripts[slot])[i];}
API(rng) u32 rng(u32 i){const u32 words[]={u32(manager.script_rng.seed)|(u32(manager.script_rng.reserved)<<16),manager.script_rng.calls,u32(manager.visual_rng.seed)|(u32(manager.visual_rng.reserved)<<16),manager.visual_rng.calls};return words[i];}

#include "../../cpp/game/AnmOpcodes.hpp"
API(template_word) u32 template_word(u32 i,u32 n){return fields(resource.templates->scripts[i])[n];}
API(texture_count) u32 texture_count(){return resource.textures.size();}
API(sprite_count) u32 sprite_count(){return resource.sprites.size();}
API(script_count) u32 script_count(){return resource.scripts.size();}
API(sprite_word) u32 sprite_word(u32 i,u32 n){
 const auto& s=resource.sprites[i];const auto& t=resource.textures[s.texture];
 const float right=s.x+s.width,bottom=s.y+s.height;
 const u32 descriptor[]={u32(resource.templates->scripts[0].file_index),s.texture,s.texture,word(s.x),word(s.y),word(right),word(bottom),word(float(t.height)),word(float(t.width)),word(s.u0),word(s.v0),word(s.u1),word(s.v1),word(s.height),word(s.width),word(1),word(1)};
 return descriptor[n];
}
API(script_id) i32 script_id(u32 i){return resource.scripts[i].source_id;}
API(script_offset) u32 script_offset(u32 i){return resource.scripts[i].file_offset;}
API(script_size) u32 script_size(u32 i){return resource.scripts[i].bytes.size();}
API(script_data) const u8* script_data(u32 i){return resource.scripts[i].bytes.data();}
API(canonical) u32 canonical(u32 op){return anm_canonical_opcode(u16(op));}
