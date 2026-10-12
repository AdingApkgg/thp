#include "../../cpp/game/EnemyManager.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
struct World:EnemyFrameWorld{void clear_shot_targets(Enemy*)override{}};
static EnemyState enemy;static EnemyEnvironment environment;static EnemyGlobals globals(enemy,environment);
static EclContext context;static EnemySpawn descriptor;static EclProgram program;static EnemyCommandEnvironment commands;static World world;
static EnemyManager manager(program,environment,commands,world);static Enemy peer;
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(run_case) i32 run_case(const EclInstruction* instruction,u32 flags,u32 n){
 enemy={};context={};context.instruction=instruction;enemy.flags=flags;enemy.instance_id=123+n;
 enemy.current.position={-99.5f+n*32.25f,27.75f-n*9.5f,9};
 u32 inherited[12];for(u32 i=0;i<12;++i)inherited[i]=0x12340000+i*100+n;std::memcpy(enemy.integers,inherited,48);
 const float floats[]={.125f+n*13.5f,-20.25f+n*11.25f};const i32 ints[]={i32(100+n),i32(1000+n),i32(n)-1};
 std::memcpy(context.stack.data+64,floats,8);std::memcpy(context.stack.data+72,ints,12);
 const char* name=nullptr;return enemy_th16_spawn_parameters(enemy,context,globals,descriptor,name);
}
API(value) u32 value(u32 n){u32 v;std::memcpy(&v,reinterpret_cast<const u8*>(&descriptor)+n*4,4);return v;}
API(guard) i32 guard(u32 op,u32 boss,u32 count,u32 capacity){
 // Deliberately missing subroutine: -2 proves the actual command reached
 // allocation; 0 proves the native guard suppressed that attempt.
 alignas(4) u8 bytes[52]{};auto* cmd=reinterpret_cast<EclInstruction*>(bytes);cmd->opcode=u16(op);cmd->length=52;
 const u32 namesize=12;std::memcpy(bytes+16,&namesize,4);std::memcpy(bytes+20,"MapleEnemy",11);
 commands={};commands.manager=&manager;commands.th16_boss_ids[0]=boss?11:0;
 peer.state.instance_id=11;peer.state.manager_link.value=&peer;peer.state.manager_link.next=nullptr;
 manager.first=boss?&peer.state.manager_link:nullptr;manager.count=count;manager.spawn_capacity=capacity;manager.last_error=0;
 EclContext c;c.instruction=cmd;EnemyScriptServices services(enemy,environment,commands);const i32 result=services.command(c);
 manager.first=nullptr;manager.count=0;manager.last_error=0;return result;
}
