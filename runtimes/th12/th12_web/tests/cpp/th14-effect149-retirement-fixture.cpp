#include "../../cpp/game/AnmManager.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;static AnmResource resource,fallback;
static std::vector<std::vector<u32>> rows;static std::vector<u32> geometry;static u32 creation_begin;
static u32 float_bits(float v){u32 n;std::memcpy(&n,&v,4);return n;}
static std::vector<u32> expanded_live_fields(const AnmVm& v){std::vector<u32> out={v.sprite?u32(v.sprite_index):u32(-1),v.flags&1,v.drawing_mode(),v.color,v.secondary_color,v.layer,v.flags2,u32(v.timer.previous),u32(v.timer.current),float_bits(v.timer.fractional),u32(v.age.previous),u32(v.age.current),float_bits(v.age.fractional)};

 for(const float x:{v.script_position.x,v.script_position.y,v.script_position.z,v.rotation.x,v.rotation.y,v.rotation.z,v.angular_velocity.x,v.angular_velocity.y,v.angular_velocity.z,v.scale.x,v.scale.y,v.extra_scale.x,v.extra_scale.y,v.texture_scale.x,v.texture_scale.y,v.uv_offset.x,v.uv_offset.y,v.scroll_velocity.x,v.scroll_velocity.y,v.sprite_size.x,v.sprite_size.y})out.push_back(float_bits(x));

 for(const auto& uv:v.uv){out.push_back(float_bits(uv.x));out.push_back(float_bits(uv.y));}for(i32 i:v.integers)out.push_back(u32(i));for(float x:v.floats)out.push_back(float_bits(x));out.push_back(v.instruction?u32(reinterpret_cast<const u8*>(v.instruction)-reinterpret_cast<const u8*>(v.script_begin)):u32(-1));return out;}



template<class T,u32 N> static void append_interpolator(std::vector<u32>& out,const Interpolator<T,N>& v){

 for(const auto* a:{v.start,v.end,v.initial_tangent,v.final_tangent})for(u32 n=0;n<N;++n){u32 word;std::memcpy(&word,a+n,4);out.push_back(word);}

 for(u32 x:{u32(v.timer.previous),u32(v.timer.current),float_bits(v.timer.fractional),v.timer.flags,u32(v.duration),u32(v.mode)})out.push_back(x);

}




static std::vector<u32> serialize(const AnmVm* vm){
   std::vector<u32> row={vm->id,u32(vm->file_index),u32(vm->script_index),u32(vm->timer.previous),u32(vm->timer.current),float_bits(vm->timer.fractional),u32(vm->pending_interrupt),u32(vm->age.current)};

   const auto extra=expanded_live_fields(*vm);row.insert(row.end(),extra.begin()+1,extra.end());for(float x:{vm->position.x,vm->position.y,vm->position.z})row.push_back(float_bits(x));row.push_back((vm->th13_native_flags>>17)&3u); for(u32 x:{vm->blend_mode(),u32((vm->flags&0x800)!=0),u32((vm->flags&0x200)!=0),u32((vm->flags&0x400)!=0),(vm->flags>>18)&3u,(vm->flags>>20)&3u,vm->th13_native_flags>>30,u32((vm->th13_native_flags&0x8000)!=0)})row.push_back(x); for(float x:{vm->extra_floats.x,vm->extra_floats.y,vm->extra_floats.z})row.push_back(float_bits(x));for(i32 x:vm->extra_integers)row.push_back(u32(x));for(float x:{vm->random_scale.x,vm->random_scale.y})row.push_back(float_bits(x));row.push_back(u32(vm->random_bound));row.push_back(float_bits(vm->scale_velocity.x));row.push_back(float_bits(vm->scale_velocity.y));append_interpolator(row,vm->position_interpolation);append_interpolator(row,vm->color_interpolation);append_interpolator(row,vm->alpha_interpolation);append_interpolator(row,vm->rotation_interpolation);append_interpolator(row,vm->scale_interpolation);append_interpolator(row,vm->color2_interpolation);append_interpolator(row,vm->alpha2_interpolation);append_interpolator(row,vm->scroll_x_interpolation);append_interpolator(row,vm->scroll_y_interpolation);append_interpolator(row,vm->extra_scale_interpolation);append_interpolator(row,vm->texture_scale_interpolation);for(float x:{vm->child_position.x,vm->child_position.y,vm->child_position.z,vm->pivot.x,vm->pivot.y,vm->slowdown_factor})row.push_back(float_bits(x));

row.push_back(vm->parent?vm->parent->id:0);row.push_back(vm->timer.flags);row.push_back(vm->age.flags);

for(const Matrix4* m:{&vm->sprite_matrix,&vm->transform_matrix,&vm->uv_matrix})for(float x:m->m)row.push_back(float_bits(x));

for(const auto* n:{vm->registry.next,vm->registry.previous,vm->child.next,vm->child.previous})row.push_back(n?n->value->id:0);

for(u32 x:{u32(vm->saved_timer.previous),u32(vm->saved_timer.current),float_bits(vm->saved_timer.fractional),u32(vm->saved_timer.rate!=nullptr),vm->saved_timer.flags,vm->saved_instruction?u32(uintptr_t(vm->saved_instruction)-uintptr_t(vm->script_begin)):0xffffffffu,u32(vm->sprite_frame),vm->inherited_color})row.push_back(x);

return row;
}
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(open) u32 open(const u8* a,u32 an,const u8* e,u32 en){manager.clear();resource={};fallback={};manager.rate=1;manager.script_rng={12345,0,0};manager.visual_rng={54321,0,0};if(!fallback.open(a,an))return 0;manager.fallback_sprites=&fallback;if(!manager.prepare_resource(fallback,3))return 0;return resource.open(e,en)&&manager.prepare_resource(resource,3);}
API(begin) u32 begin(float rate,u32 seed,u32 z,float x){manager.clear();manager.rate=rate;manager.script_rng={u16(seed),0,0};manager.visual_rng={54321,0,0};creation_begin=anm_creation_count();Vec3 p{17+x,123,0};std::memcpy(&p.z,&z,4);float angle=.7f;return manager.create(resource,149,3,~0u,false,false,&p,nullptr,nullptr,false,&angle)!=nullptr;}
API(step) u32 step(){return manager.update(false)&&manager.update(true);}
API(capture) u32 capture(){rows.clear();geometry.clear();for(u32 n=creation_begin;n<anm_creation_count();++n){const u32 id=u32(anm_creation_value(n,5));const auto* vm=manager.find(id);if(!vm)continue;rows.push_back(serialize(vm));if(vm->script_index==143){Vec3 out[4];if(!anm_quad_positions(*vm,out,manager.render_space))return 0;geometry.push_back(id);for(const auto& p:out)for(float v:{p.x,p.y,p.z})geometry.push_back(float_bits(v));}}return rows.size()==manager.active_count();}
API(count) u32 count(){return rows.size();}
API(field) u32 field(u32 n,u32 k){return rows.at(n).at(k);}
API(geometry_count) u32 geometry_count(){return geometry.size();}
API(geometry_field) u32 geometry_field(u32 k){return geometry.at(k);}
API(created) u32 created(){return anm_creation_count()-creation_begin;}
API(creation_id) u32 creation_id(u32 n){return u32(anm_creation_value(creation_begin+n,5));}
API(rng) u32 rng(u32 k){const u32 a[]={u32(manager.script_rng.seed)|(u32(manager.script_rng.reserved)<<16),manager.script_rng.calls,u32(manager.visual_rng.seed)|(u32(manager.visual_rng.reserved)<<16),manager.visual_rng.calls};return a[k];}

API(layer_head) u32 layer_head(u32 n){const auto* vm=manager.layer_first(n);return vm?vm->id:0;}
