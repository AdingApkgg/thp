#include "../../cpp/game/EnemyCommands.hpp"
#include "../../cpp/game/EnemyScript.hpp"
#include "../../cpp/game/EnemyAnimations.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include <algorithm>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static EnemyState e;static EnemyEnvironment env;static u32 events[32][4],count,ticks;static i32 counts[3],count_size;static u8 bytes[256];
static void record(u32 kind,u32 a=0,u32 b=0,u32 c=0){const u32 row[]={kind,a,b,c};std::memcpy(events[count++],row,sizeof row);}
struct Services:Th16LooseAnimationServices{
 bool construct(i32 file,i32 script)override{record(0,file,script,0xffffffff);return true;}
 bool register_effect()override{record(1,37);return true;}
 bool lookup_effect()override{record(2);return true;}
 bool tick()override{record(3);++ticks;const i32 value=counts[std::min(ticks,u32(count_size-1))];std::memcpy(bytes+24,&value,4);return true;}
};
API(animation) i32 animation(i32 file,i32 script,i32 c0,i32 c1,i32 c2,i32 size){count=ticks=0;counts[0]=c0;counts[1]=c1;counts[2]=c2;count_size=size;std::memset(bytes,0,sizeof bytes);auto* cmd=reinterpret_cast<EclInstruction*>(bytes);cmd->opcode=339;cmd->length=28;std::memcpy(bytes+16,&file,4);std::memcpy(bytes+20,&script,4);std::memcpy(bytes+24,&c0,4);EclContext c;c.instruction=cmd;EnemyGlobals g(e,env);Services services;return enemy_th16_loose_animation_command(c,g,services);}
API(event_count) u32 event_count(){return count;}
API(animation308) i32 animation308(i32 file,i32 script){count=ticks=0;std::memset(bytes,0,sizeof bytes);auto* cmd=reinterpret_cast<EclInstruction*>(bytes);cmd->opcode=308;cmd->length=24;std::memcpy(bytes+16,&file,4);std::memcpy(bytes+20,&script,4);EclContext c;c.instruction=cmd;EnemyGlobals g(e,env);Services services;return enemy_th16_loose_animation_command(c,g,services);}
API(event) u32 event(u32 n,u32 f){return events[n][f];}
API(copy) i32 copy(u32 length,u32 seed){e={};for(u32 i=0;i<64;++i)e.th16_death_script[i]=char(seed+i*3);std::memset(bytes,0,sizeof bytes);auto* cmd=reinterpret_cast<EclInstruction*>(bytes);cmd->opcode=556;cmd->length=21+length;for(u32 i=0;i<length;++i)bytes[20+i]=65+i%26;EclContext c;c.instruction=cmd;return enemy_th16_death_script_command(e,c);}
API(copy_value) u32 copy_value(u32 n){return u8(e.th16_death_script[n]);}
static AnmResource resource;static AnmManager manager;static EnemyAnimations animations(manager);static EnemyCommandEnvironment commands;static AnmVm* created;static u32 registered;
static void setup_positioned(i32 file,u32 x,u32 y,u32 z){
 manager.clear();resource={};resource.scripts.resize(1);const AnmInstruction code[]={{i16(anm_canonical_opcode(0)),8,32760,0},{-1,8,32760,0}};resource.scripts[0].bytes.resize(sizeof code);std::memcpy(resource.scripts[0].bytes.data(),code,sizeof code);
 for(u32 n=0;n<16;++n)animations.resources[n]={&resource,u16(n+10)};registered=0;animations.th16_register_effect=[](void*,u32 id){created=manager.find(id);++registered;return created!=nullptr;};commands.animations=&animations;e={};e.current.position={float_bits(x),float_bits(y),float_bits(z)};
 std::memset(bytes,0,sizeof bytes);std::memcpy(bytes+16,&file,4);
}
static i32 run_positioned(u16 opcode,u16 length){auto* cmd=reinterpret_cast<EclInstruction*>(bytes);cmd->opcode=opcode;cmd->length=length;EclContext c;c.instruction=cmd;EnemyScriptServices services(e,env,commands);return services.command(c);}
API(positioned307) i32 positioned307(i32 file,u32 x,u32 y,u32 z){setup_positioned(file,x,y,z);return run_positioned(307,24);}
API(positioned338) i32 positioned338(i32 file,u32 x,u32 y,u32 z,u32 dx,u32 dy,u32 angle){setup_positioned(file,x,y,z);std::memcpy(bytes+24,&dx,4);std::memcpy(bytes+28,&dy,4);std::memcpy(bytes+32,&angle,4);return run_positioned(338,36);}
API(positioned_word) u32 positioned_word(u32 n){const u32 words[]={created->layer,created->flags2,float_bits(created->position.x),float_bits(created->position.y),float_bits(created->position.z),float_bits(created->rotation.z),created->reserved_418,registered,u32(e.relative_angle.duration)};return words[n];}
