#include "../../cpp/game/EnemyManager.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static EnemyState e;static EnemyEnvironment env;static EnemyCommandEnvironment commands;static EclContext c;
alignas(4) static u8 instruction[36];static u32 initial[192];
API(code_pointer) u8* code_pointer(){return instruction;}
API(initial_pointer) u32* initial_pointer(){return initial;}
API(run_case) i32 run_case(i32 difficulty){
 e={};env.difficulty=difficulty;c={};c.instruction=reinterpret_cast<EclInstruction*>(instruction);c.stack.frame_base=32;std::memcpy(c.stack.data,initial,sizeof(initial));
 EnemyScriptServices services(e,env,commands);return services.command(c);
}
API(value) u32 value(u32 n){u32 v;std::memcpy(&v,c.stack.data+n*4,4);return v;}
