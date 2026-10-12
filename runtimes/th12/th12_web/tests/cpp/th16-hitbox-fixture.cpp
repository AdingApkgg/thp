#include "../../cpp/game/EnemyManager.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static EnemyState e;static EnemyEnvironment env;static EnemyCommandEnvironment commands;
API(run_case) i32 run_case(u32 op,u32 x,u32 y,i32 credit){
 e={};e.hitbox=e.collision_box={24,24};e.th16_chapter_credit=credit;commands.th16_chapter_spawned=-1;
 alignas(4) u8 bytes[24]{};auto* cmd=reinterpret_cast<EclInstruction*>(bytes);cmd->opcode=u16(op);cmd->length=24;std::memcpy(bytes+16,&x,4);std::memcpy(bytes+20,&y,4);
 EclContext c;c.instruction=cmd;EnemyScriptServices services(e,env,commands);return services.command(c);
}
API(value) u32 value(u32 n){return n==0?float_bits(e.hitbox.x):n==1?float_bits(e.hitbox.y):n==2?float_bits(e.collision_box.x):n==3?float_bits(e.collision_box.y):n==4?u32(e.th16_chapter_credit):u32(commands.th16_chapter_spawned);}
