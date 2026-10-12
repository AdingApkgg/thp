#include "../../cpp/game/EnemyManager.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static Enemy owner,targets[4];static EnemyEnvironment environment;static EnemyCommandEnvironment commands;static EclProgram program;
struct World:EnemyFrameWorld{void clear_shot_targets(Enemy*)override{}};static World world;
static EnemyManager manager(program,environment,commands,world);
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(begin) i32 begin(u32 op,i32 id,const u32* initial,const u32* rows,u32 count){
    owner.state={};std::memcpy(&owner.state.previous,initial,52*4);
    for(u32 j=0;j<count;++j){auto& e=targets[j].state;e={};e.instance_id=signed_bits(rows[j*4]);std::memcpy(&e.current.position,rows+j*4+1,12);e.manager_link={&targets[j],j+1<count?&targets[j+1].state.manager_link:nullptr,j?&targets[j-1].state.manager_link:nullptr};}
    manager.first=count?&targets[0].state.manager_link:nullptr;manager.last=count?&targets[count-1].state.manager_link:nullptr;
    // Exercise ECL argument references through production dispatch.
    owner.state.parent_instance_id=u32(id);alignas(4) u8 bytes[20]{};auto* instruction=reinterpret_cast<EclInstruction*>(bytes);instruction->opcode=u16(op);instruction->length=20;instruction->references=1;const i32 ref=-9909;std::memcpy(bytes+16,&ref,4);
    EclContext context;context.instruction=instruction;EnemyScriptServices services(owner.state,environment,commands);return services.command(context);
}
API(value) u32 value(u32 n){u32 word;std::memcpy(&word,reinterpret_cast<const u8*>(&owner.state.previous)+n*4,4);return word;}
