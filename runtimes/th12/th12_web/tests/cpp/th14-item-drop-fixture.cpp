#include "../../cpp/game/ItemManager.hpp"
#include "../../cpp/game/EnemyManager.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmEnvironment animations;static AnmResource resource;static ItemWorld item_world;
static std::unique_ptr<ItemManager> items;static EnemyState enemy;static EnemyEnvironment environment;
struct World:EnemyFrameWorld{bool drop_items(EnemyState& e)override{return items->drop(e.drops,e.current.position);}void clear_shot_targets(Enemy*)override{}};
static World world;static EnemyCommandEnvironment commands;static EclProgram program;
static EnemyManager manager(program,environment,commands,world);
API(begin) i32 begin(u32 seed,u32 flags,i32 primary,i32 n,float x,float y,float z,float sx,float sy){
    animations.script_rng={54321,0,123};animations.rate=1;animations.visual_rng={u16(seed),0,0};resource={};resource.scripts.resize(294);
    const AnmInstruction code[]={{i16(anm_canonical_opcode(2)),8,0,0},{-1,8,0,0}};
    for(auto& s:resource.scripts){s.bytes.resize(sizeof code);std::memcpy(s.bytes.data(),code,sizeof code);}
    items=std::make_unique<ItemManager>(resource,animations,item_world,7);
    enemy={};enemy.current.position={x,y,z};enemy.drops.primary=primary;enemy.drops.counts[0]=n%4;enemy.drops.counts[1]=(n*3)%5;enemy.drops.counts[12]=100+n;enemy.drops.spread={sx,sy};
    commands.th14_run_flags=flags;EclInstruction cmd{};cmd.opcode=509;cmd.length=16;EclContext context;context.instruction=&cmd;
    EnemyScriptServices services(enemy,environment,commands);return services.command(context);
}
API(value) u32 value(u32 n){return n==0?u32(enemy.drops.primary):n<14?u32(enemy.drops.counts[n-1]):n==14?animations.visual_rng.seed:animations.visual_rng.calls;}
API(spawn_count) u32 spawn_count(){return items->th14_spawn_count;}
API(spawn_value) u32 spawn_value(u32 n,u32 k){const auto& i=items->at(599-n);const u32 a[]={u32(i.type),float_bits(i.position.x),float_bits(i.position.y),float_bits(i.position.z),float_bits(i.velocity.x),float_bits(i.velocity.y),u32(i.delay)};return a[k];}

API(other_rng) u32 other_rng(u32 n){return n?animations.script_rng.calls:animations.script_rng.seed;}
