#include "../../cpp/game/EnemyCommands.hpp"
#include "../../cpp/game/LaserManager.hpp"
#include "../../cpp/game/EclContext.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
namespace {
AnmResource resource;AnmEnvironment animations;LaserWorld world;
LaserManager manager(resource,animations,world);
EnemyState enemy;EnemyEnvironment environment;EnemyGlobals globals(enemy,environment);
std::vector<u32> result;
u8* request(LaserState* b){return b->type==1?reinterpret_cast<Th14LaserInfinite*>(b)->request:b->type==2?reinterpret_cast<Th14LaserCurve*>(b)->path.request:reinterpret_cast<Th14LaserShell*>(b)->request;}
LaserState* create(u32 kind,const u32* p){
    LaserState* b=kind==1?&((new Th14LaserInfinite{})->base):kind==2?&((new Th14LaserCurve{})->base):&((new Th14LaserShell{})->base);
    b->type=i32(kind);b->position={float_bits(p[0]),float_bits(p[1]),float_bits(p[2])};b->angle=float_bits(p[3]);b->length=float_bits(p[4]);b->width=float_bits(p[5]);b->speed=float_bits(p[6]);b->id=i32(p[7]);std::memcpy(request(b),p+8,44);manager.append(*b);return b;
}
}
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(run) i32 run(u32 op,u32 kind,const u32* before,const u32* args,u32 local){
    manager.clear();create(kind,before);create(kind,before+19);alignas(4)u8 data[32]{};auto* cmd=reinterpret_cast<EclInstruction*>(data);cmd->opcode=u16(op);cmd->length=28;std::memcpy(data+16,args,12);EclContext context;
    if(local){cmd->references=7;context.stack.top=12;std::memcpy(context.stack.data,args,12);for(u32 j=0;j<3;++j){const u32 reference=j==0?0:float_bits(float(j*4));std::memcpy(data+16+j*4,&reference,4);}}
    context.instruction=cmd;EnemyCommandEnvironment commands;commands.lasers=&manager;const auto status=enemy_th14_state_command(enemy,context,globals,commands);result.clear();
    for(auto* b=manager.first();b;b=b->next){const u32 state[]={float_bits(b->position.x),float_bits(b->position.y),float_bits(b->position.z),float_bits(b->angle),float_bits(b->length),float_bits(b->width),float_bits(b->speed),u32(b->id)};result.insert(result.end(),state,state+8);const auto* r=request(b);for(u32 j=0;j<11;++j){u32 v;std::memcpy(&v,r+4*j,4);result.push_back(v);}}
    return status;
}
API(value) u32 value(u32 n){return result.at(n);}
