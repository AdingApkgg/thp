#include "../../cpp/game/EnemyManager.hpp"
#include "../../cpp/game/EclRoutes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
struct World:EnemyFrameWorld{void clear_shot_targets(Enemy*)override{}};
static EclProgram program;
static EnemyEnvironment env;
static EnemyCommandEnvironment commands;
static World world;
static EnemyManager manager(program,env,commands,world);
static EnemyState enemy;
static Enemy peers[3];
static void setup(u32 length){
 manager.first=length?&peers[0].state.manager_link:nullptr;
 for(u32 j=0;j<3;++j){auto& e=peers[j].state;e.instance_id=(j+1)*11;e.manager_link.value=&peers[j];e.manager_link.next=j+1<length?&peers[j+1].state.manager_link:nullptr;}
}
API(registration) i32 registration(u32 flags,u32 mf,i32 prior,i32 slot){
 enemy={};commands={};commands.manager=&manager;enemy.flags=flags;enemy.boss_slot=prior;enemy.instance_id=22;commands.manager_flags=mf;
 for(u32 j=0;j<4;++j)commands.th16_boss_ids[j]=100+j;
 alignas(4) u8 bytes[20]{};auto* cmd=reinterpret_cast<EclInstruction*>(bytes);cmd->opcode=512;cmd->length=20;std::memcpy(bytes+16,&slot,4);
 EclContext c;c.instruction=cmd;EnemyScriptServices services(enemy,env,commands);return services.command(c);
}
API(value) u32 value(u32 n){return n==0?enemy.flags:n==1?u32(enemy.boss_slot):n==2?commands.manager_flags:u32(commands.th16_boss_ids[n-3]);}
API(lookup) u32 lookup(u32 length,u32 slot,i32 id){setup(length);commands.th16_boss_ids[slot]=id;auto* p=manager.th16_boss(slot);for(u32 j=0;j<3;++j)if(p==&peers[j].state)return j+1;return 0;}
API(wait) i32 wait(u32 length,u32 mask){setup(length);commands.manager=&manager;for(u32 j=0;j<4;++j)commands.th16_boss_ids[j]=mask&(1u<<j)?11:0;EclInstruction cmd{};cmd.opcode=520;EclContext c;c.instruction=&cmd;EnemyScriptServices services(enemy,env,commands);return services.command(c);}
API(route) i32 route(u32 op){return ecl_manager_route(op);}
static u32 visible_count,visible_ids[16],visible_values[16];
API(flags) i32 flags(u32 op,u32 initial,u32 bits){
 enemy={};commands={};commands.manager=&manager;enemy.flags=initial;visible_count=0;for(u32 j=0;j<16;++j)enemy.animation_handle(j)=100+j;
 commands.animation_visibility=[](u32 id,bool visible,void*){visible_ids[visible_count]=id;visible_values[visible_count++]=visible;};
 alignas(4) u8 bytes[20]{};auto* cmd=reinterpret_cast<EclInstruction*>(bytes);cmd->opcode=u16(op);cmd->length=20;std::memcpy(bytes+16,&bits,4);
 EclContext c;c.instruction=cmd;EnemyScriptServices services(enemy,env,commands);return services.command(c);
}
API(visibility_count) u32 visibility_count(){return visible_count;}
API(visibility_value) u32 visibility_value(u32 j,u32 n){return n?visible_values[j]:visible_ids[j];}
API(spell_practice) u32 spell_practice(i32 value,u32 floating){env.spell_practice_id=value;EnemyGlobals g(enemy,env);return floating?float_bits(float(g.floating(-9907))):u32(g.integer(-9907));}
