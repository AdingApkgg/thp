#include "../../cpp/game/PlayerMotion.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmResource main_file,season_file;static AnmManager animations;static ShtResource main_sht,season_sht;static u32 creation_start;
struct World:PlayerMotionWorld{};static World world;static PlayerMotion motion(main_file,main_file,animations,world,9,7);
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(open) i32 open(const u8* p,u32 n,u32 sub){return (sub?season_sht:main_sht).open(p,n);}
API(begin) i32 begin(i32 character,i32 season,i32 old,i32 old_season,i32 power,i32 points,i32 focus){
 animations.clear();
 for(auto* file:{&main_file,&season_file}){file->scripts.resize(20);for(auto& script:file->scripts){script.bytes.resize(16);const AnmInstruction h{i16(anm_canonical_opcode(2)),8,0,0},end{-1,8,0,0};std::memcpy(script.bytes.data(),&h,8);std::memcpy(script.bytes.data()+8,&end,8);}}
 motion.state={};motion.options={};motion.last_error=0;motion.state.x=-321;motion.state.y=50319;motion.state.option_count=old;motion.th16_season_count=old_season;motion.state.focused=focus;
 const u32 offsets[]={0,0x54,0x58,0x5c,0x60,0x64,0x68,0x6c,0x70,0xd0,0xd4};
 for(u32 i=0;i<12;++i)for(auto k:offsets){const u32 v=17+i*31+k;std::memcpy(reinterpret_cast<u8*>(&motion.options[i])+k,&v,4);}
 GameEconomy economy;economy.power=power;economy.power_step=100;economy.max_power=400;economy.th16_season.count=points;
 creation_start=anm_creation_count();return motion.rebuild_options_th16(main_sht.header,season_sht.header,season_file,economy,character,season)?1:motion.last_error;
}
API(creations) u32 creations(){return anm_creation_count()-creation_start;}
API(created_script) i32 created_script(u32 n){return anm_creation_value(creation_start+n,0);}
API(value) u32 value(u32 n){return n==0?motion.state.option_count:n==1?motion.th16_requested_count:motion.th16_season_count;}
API(option) u32 option(u32 i,u32 k){const auto& o=motion.options[i];const u32 a[]={u32(o.state),u32(o.target_x),u32(o.target_y),u32(o.x),u32(o.y),u32(o.normal_x),u32(o.normal_y),u32(o.focus_x),u32(o.focus_y),u32(o.index),u32(o.snap)};return a[k];}
API(animation) u32 animation(u32 n,u32 k){const auto id=anm_creation_value(creation_start+n,5);const auto* vm=animations.find(id);if(!vm)return 0;return k==0?vm->flags2:k==1?vm->layer:float_bits(vm->position.y);}
