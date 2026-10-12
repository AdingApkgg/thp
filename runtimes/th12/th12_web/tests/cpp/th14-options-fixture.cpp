#include "../../cpp/game/PlayerMotion.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmResource file;static AnmManager animations;static ShtResource sht;static u32 creation_start;
struct World:PlayerMotionWorld{};static World world;static PlayerMotion motion(file,file,animations,world);
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(open) i32 open(const u8* p,u32 n){return sht.open(p,n);}
API(begin) i32 begin(i32 slot,i32 old,i32 power,i32 focus){
 animations.clear();file.scripts.resize(15);
 // Controlled ANM binder/update: a non-rendering instruction keeps each VM alive.
 for(auto& script:file.scripts){script.bytes={0x02,0x00,0x08,0x00,0x00,0x00,0x00,0x00};}
 motion.state={};motion.options={};motion.last_error=0;motion.state.x=-321;motion.state.y=50319;motion.state.option_count=old;motion.state.option_angle=1;motion.state.focused=focus;
 GameEconomy economy;economy.power=power;economy.power_step=40;economy.max_power=160;
 creation_start=anm_creation_count();return motion.rebuild_options(sht.header,economy,slot)?1:motion.last_error;
}
API(creations) u32 creations(){return anm_creation_count()-creation_start;}
API(created_script) i32 created_script(u32 n){return anm_creation_value(creation_start+n,0);}
API(value) u32 value(u32 n){return n?float_bits(motion.state.option_angle):u32(motion.state.option_count);}
API(option) u32 option(u32 i,u32 k){const auto& o=motion.options[i];const u32 a[]={u32(o.state),u32(o.target_x),u32(o.target_y),u32(o.x),u32(o.y),u32(o.normal_x),u32(o.normal_y),u32(o.focus_x),u32(o.focus_y),u32(o.index),u32(o.snap)};return a[k];}
API(script) i32 script(u32 i,u32 aux){const auto& o=motion.options[i];const auto* vm=animations.find(aux?o.auxiliary:o.animation);return vm?vm->script_index:-1;}
API(animation) u32 animation(u32 i,u32 aux,u32 k){const auto& o=motion.options[i];const auto* vm=animations.find(aux?o.auxiliary:o.animation);if(!vm)return 0;return k==0?vm->flags2:k==1?vm->layer:float_bits(vm->position.y);}
