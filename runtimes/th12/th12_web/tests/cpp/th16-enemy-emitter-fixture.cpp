#include "../../cpp/game/EnemyScript.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static EnemyState enemy;
static EnemyEnvironment environment;
static EnemyCommandEnvironment commands;
static u8 packed[0x39c0];
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(run) i32 run(u32 op,i32 difficulty,const u8* input,const u32* args){
    enemy={};environment.difficulty=difficulty;
    std::memcpy(enemy.th16_emitters.records,input,0x3800);std::memcpy(enemy.th16_emitters.cursors,input+0x3800,0x40);
    std::memcpy(enemy.th16_emitters.bases,input+0x3840,0xc0);std::memcpy(enemy.th16_emitters.origins,input+0x3900,0xc0);
    alignas(4) u8 code[80]{};auto* cmd=reinterpret_cast<EclInstruction*>(code);cmd->opcode=u16(op);cmd->length=80;std::memcpy(code+16,args,64);
    EclContext context;context.instruction=cmd;return EnemyScriptServices(enemy,environment,commands).command(context);
}
API(output) const u8* output(){
    std::memcpy(packed,enemy.th16_emitters.records,0x3800);std::memcpy(packed+0x3800,enemy.th16_emitters.cursors,0x40);
    std::memcpy(packed+0x3840,enemy.th16_emitters.bases,0xc0);std::memcpy(packed+0x3900,enemy.th16_emitters.origins,0xc0);return packed;
}
