#include "../../cpp/game/EnemyManager.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static EnemyState enemy;
static EnemyEnvironment environment;
static EnemyGlobals globals(enemy,environment);
static EclContext context;
static EnemySpawn descriptor;
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(run_case) i32 run_case(const EclInstruction* instruction,u32 flags,u32 n){
    enemy={};context={};context.instruction=instruction;enemy.flags=flags;enemy.instance_id=123+n;
    enemy.current.position={-99.5f+n*32.25f,27.75f-n*9.5f,9};
    u32 inherited[12];for(u32 i=0;i<12;++i)inherited[i]=0x12340000+i*100+n;std::memcpy(enemy.integers,inherited,48);
    const float floats[]={.125f+n*13.5f,-20.25f+n*11.25f};const i32 ints[]={i32(100+n),i32(1000+n),i32(n)-1};
    std::memcpy(context.stack.data+64,floats,8);std::memcpy(context.stack.data+72,ints,12);
    const char* name=nullptr;return enemy_th14_spawn_parameters(enemy,context,globals,descriptor,name);
}
API(value) u32 value(u32 n){u32 v;std::memcpy(&v,reinterpret_cast<const u8*>(&descriptor)+n*4,4);return v;}
API(mode_value) u32 mode_value(i32 value,u32 floating){environment.spell_practice_id=value;return floating?float_bits(float(globals.floating(-9907))):u32(globals.integer(-9907));}
