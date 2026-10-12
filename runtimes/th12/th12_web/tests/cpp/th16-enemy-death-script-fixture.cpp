#include "../../cpp/game/EnemyFrame.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static Enemy enemy;static EnemyEnvironment environment;static EnemyCommandEnvironment commands;
static EclResource resource;static EclProgram program;static AnmManager manager;static EnemyAnimations animations(manager);
struct World:EnemyFrameWorld{
 void clear_shot_targets(Enemy*)override{}
 u32 drops=0;
 bool drop_items_now_th16(EnemyState& e)override{++drops;return e.th16_death_script[0]&&e.script_owner->script.root.stack.top==dirty;}
 u32 dirty=0;
};
static World world;
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(run) i32 run(const u8* code,u32 length,u32 threads,u32 dirty){
 enemy={};enemy.state.script_owner=&enemy;enemy.state.death_sound=enemy.state.death_animation=-1;enemy.state.drops.primary=7;
 resource.bytes.assign(16,0);resource.bytes.insert(resource.bytes.end(),code,code+length);resource.subroutines={{"Death",0,length+16}};program.definitions={{&resource,0}};
 enemy.script.initialize_context();enemy.script.program=&program;enemy.script.root.stack.top=enemy.script.root.stack.frame_base=dirty;
 EnemyScriptServices services(enemy.state,environment,commands);world.drops=0;world.dirty=dirty;
 for(u32 n=0;n<threads;++n){auto* node=new EclThread{};auto* context=new EclContext{};node->value=context;node->next=enemy.script.threads.next;node->previous=&enemy.script.threads;if(node->next)node->next->previous=node;enemy.script.threads.next=node;}
 alignas(4) u8 bytes[28]{};auto* ins=reinterpret_cast<EclInstruction*>(bytes);ins->opcode=556;ins->length=28;std::memcpy(bytes+20,"Death",6);
 EclContext c;c.instruction=ins;if(services.command(c))return -99;
 const i32 result=enemy_death(enemy.state,animations,world,&services);
 // Name points into this function's command buffer, so a retained pointer is a failure.
 return result;
}
API(value) u32 value(u32 n){auto& c=enemy.script.root;
 switch(n){case 0:return float_bits(c.time);case 1:return reinterpret_cast<const u8*>(c.instruction)-resource.bytes.data()-16;case 2:return c.stack.top;case 3:return c.stack.frame_base;case 4:return c.stack.local<u32>(0);case 5:return !!enemy.state.th16_death_script[0];case 6:return !!enemy.script.threads.next;case 7:return world.drops;case 8:return enemy.state.drops.primary;}return 0;
}
