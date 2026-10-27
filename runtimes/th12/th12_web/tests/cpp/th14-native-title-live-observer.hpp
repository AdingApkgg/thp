#pragma once
// Same 303-word read-only VM representation used by the campaign observer.
// Walk live registries; never infer liveness from retained pool contents.
#include <vector>
namespace th14_title_observer {
using namespace th11;
static std::vector<u32> expanded_live_fields(const AnmVm& v){std::vector<u32> out={v.sprite?u32(v.sprite_index):u32(-1),v.flags&1,v.drawing_mode(),v.color,v.secondary_color,v.layer,v.flags2,u32(v.timer.previous),u32(v.timer.current),float_bits(v.timer.fractional),u32(v.age.previous),u32(v.age.current),float_bits(v.age.fractional)};

 for(const float x:{v.script_position.x,v.script_position.y,v.script_position.z,v.rotation.x,v.rotation.y,v.rotation.z,v.angular_velocity.x,v.angular_velocity.y,v.angular_velocity.z,v.scale.x,v.scale.y,v.extra_scale.x,v.extra_scale.y,v.texture_scale.x,v.texture_scale.y,v.uv_offset.x,v.uv_offset.y,v.scroll_velocity.x,v.scroll_velocity.y,v.sprite_size.x,v.sprite_size.y})out.push_back(float_bits(x));

 for(const auto& uv:v.uv){out.push_back(float_bits(uv.x));out.push_back(float_bits(uv.y));}for(i32 i:v.integers)out.push_back(u32(i));for(float x:v.floats)out.push_back(float_bits(x));out.push_back(v.instruction?u32(reinterpret_cast<const u8*>(v.instruction)-reinterpret_cast<const u8*>(v.script_begin)):u32(-1));return out;}



template<class T,u32 N> static void append_interpolator(std::vector<u32>& out,const Interpolator<T,N>& v){

 for(const auto* a:{v.start,v.end,v.initial_tangent,v.final_tangent})for(u32 n=0;n<N;++n){u32 word;std::memcpy(&word,a+n,4);out.push_back(word);}

 for(u32 x:{u32(v.timer.previous),u32(v.timer.current),float_bits(v.timer.fractional),v.timer.flags,u32(v.duration),u32(v.mode)})out.push_back(x);

}
inline void capture_live_rows(GameSession& session,std::vector<std::vector<u32>>& rows,u32& expected,bool& complete){
auto& manager=session.animations;expected=manager.active_count();

 std::vector<u32> seen;

 for(u32 layer=0;layer<36;++layer){auto* seed=manager.layer_first(layer);if(!seed)continue;

  auto* node=&seed->registry;u32 back=0;while(node->previous){node=node->previous;if(++back>8192)return;}

  for(u32 budget=0;node&&budget<8192;node=node->next,++budget){

   const auto* vm=node->value;if(!vm||manager.find(vm->id)!=vm)return;

   bool duplicate=false;for(u32 id:seen)if(id==vm->id)duplicate=true;if(duplicate)continue;seen.push_back(vm->id);

   std::vector<u32> row={vm->id,u32(vm->file_index),u32(vm->script_index),u32(vm->timer.previous),u32(vm->timer.current),float_bits(vm->timer.fractional),u32(vm->pending_interrupt),u32(vm->age.current)};

   const auto extra=expanded_live_fields(*vm);row.insert(row.end(),extra.begin()+1,extra.end());for(float x:{vm->position.x,vm->position.y,vm->position.z})row.push_back(float_bits(x));row.push_back((vm->th13_native_flags>>17)&3u); for(u32 x:{vm->blend_mode(),u32((vm->flags&0x800)!=0),u32((vm->flags&0x200)!=0),u32((vm->flags&0x400)!=0),(vm->flags>>18)&3u,(vm->flags>>20)&3u,vm->th13_native_flags>>30,u32((vm->th13_native_flags&0x8000)!=0)})row.push_back(x); for(float x:{vm->extra_floats.x,vm->extra_floats.y,vm->extra_floats.z})row.push_back(float_bits(x));for(i32 x:vm->extra_integers)row.push_back(u32(x));for(float x:{vm->random_scale.x,vm->random_scale.y})row.push_back(float_bits(x));row.push_back(u32(vm->random_bound));row.push_back(float_bits(vm->scale_velocity.x));row.push_back(float_bits(vm->scale_velocity.y));append_interpolator(row,vm->position_interpolation);append_interpolator(row,vm->color_interpolation);append_interpolator(row,vm->alpha_interpolation);append_interpolator(row,vm->rotation_interpolation);append_interpolator(row,vm->scale_interpolation);append_interpolator(row,vm->color2_interpolation);append_interpolator(row,vm->alpha2_interpolation);append_interpolator(row,vm->scroll_x_interpolation);append_interpolator(row,vm->scroll_y_interpolation);append_interpolator(row,vm->extra_scale_interpolation);append_interpolator(row,vm->texture_scale_interpolation);for(float x:{vm->child_position.x,vm->child_position.y,vm->child_position.z,vm->pivot.x,vm->pivot.y,vm->slowdown_factor})row.push_back(float_bits(x));

row.push_back(vm->parent?vm->parent->id:0);row.push_back(vm->timer.flags);row.push_back(vm->age.flags);

for(const Matrix4* m:{&vm->sprite_matrix,&vm->transform_matrix,&vm->uv_matrix})for(float x:m->m)row.push_back(float_bits(x));

for(const auto* n:{vm->registry.next,vm->registry.previous,vm->child.next,vm->child.previous})row.push_back(n?n->value->id:0);

for(u32 x:{u32(vm->saved_timer.previous),u32(vm->saved_timer.current),float_bits(vm->saved_timer.fractional),u32(vm->saved_timer.rate!=nullptr),vm->saved_timer.flags,vm->saved_instruction?u32(uintptr_t(vm->saved_instruction)-uintptr_t(vm->script_begin)):0xffffffffu,u32(vm->sprite_frame),vm->inherited_color})row.push_back(x);

rows.push_back(std::move(row));

  }

 }
 complete=rows.size()==expected;
}
}
