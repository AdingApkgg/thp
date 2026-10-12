#include "../../cpp/game/EnemyCommands.hpp"
#include <vector>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static EnemyState enemy;
static std::vector<u32> calls;
API(run_case) i32 run_case(u32 opcode,u32 flags,u32 bits,u32 pattern){
    enemy={};enemy.flags=flags;calls.clear();EnemyCommandEnvironment world;
    world.animation_visibility=[](u32 id,bool visible,void*){calls.push_back(id);calls.push_back(visible);};
    for(u32 i=0;i<16;++i){const u32 id=pattern==0||(pattern==2&&i%2==0)?0:100+i;if(i<10)enemy.animations[i]=id;else enemy.additional_animations[i-10]=id;}
    return enemy_th14_flags(enemy,u16(opcode),bits,world);
}
API(flags) u32 flags(){return enemy.flags;}
API(count) u32 count(){return calls.size()/2;}
API(call_value) u32 call_value(u32 i){return calls.at(i);}
