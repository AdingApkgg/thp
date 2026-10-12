#include "../../cpp/game/GameSessionResources.hpp"
#include "../../cpp/game/AnmManager.hpp"
#include "../../cpp/game/EclContext.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmResource resource,ascii;static AnmManager animations;static AnmVm vm;static u32 creation_start;
API(allocate) void* allocate(u32 size){return std::malloc(size);}
API(open) i32 open(const u8* bytes,u32 size,i32 which){return (which?ascii:resource).open(bytes,size);}
API(begin) i32 begin(i32 script,float rate){animations.clear();creation_start=anm_creation_count();animations.rate=rate;animations.fallback_sprites=&ascii;vm.initialize();vm.layer=0;if(!vm.bind_script(resource,script,7,&animations.rate))return -2;vm.flags2=0x200;return vm.update(animations);}
API(child_count) u32 child_count(){return anm_creation_count()-creation_start;}
API(child_script) i32 child_script(u32 n){return anm_creation_value(creation_start+n,0);}
API(tick) i32 tick(){return vm.update(animations);}
API(interrupt) void interrupt(i32 label){vm.interrupt(label);}
API(value) u32 value(u32 n){const u32 a[]={u32(vm.sprite_index),vm.color,vm.layer,vm.flags2,vm.flags&1,u32(vm.timer.current),float_bits(vm.timer.fractional),float_bits(vm.script_position.x),float_bits(vm.script_position.y),float_bits(vm.script_position.z),float_bits(vm.scale.x),float_bits(vm.scale.y),float_bits(vm.extra_scale.x),float_bits(vm.extra_scale.y),float_bits(vm.rotation.z)};return a[n];}
