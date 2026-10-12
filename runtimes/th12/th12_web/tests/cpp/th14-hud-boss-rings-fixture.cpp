#include "../../cpp/game/Hud.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include "../../cpp/game/EclContext.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;static AnmResource front,text;static GameEconomy economy;static EnemyCommandEnvironment enemies;
static StageCompletionState completion;static HudEffects effects;static std::unique_ptr<Hud> hud;static EnemyState bosses[2];
static u32 old[2][7]{},name_old,first;static std::vector<i32> created;
API(run) u32 run(i32 variant,i32 prior,i32 position,i32 displayed,i32 hidden){
 hud.reset();manager.clear();front={};enemies={};front.scripts.resize(256);
 const AnmInstruction code[]={{i16(anm_canonical_opcode(2)),8,0,0},{-1,8,0,0}};
 for(auto& s:front.scripts){s.bytes.resize(sizeof code);std::memcpy(s.bytes.data(),code,sizeof code);}
 hud=std::make_unique<Hud>(manager,front,text,economy,enemies,completion,effects);
 constexpr Vec3 positions[]={{12.25f,-14.5f,4.75f},{0,0,0},{80,0,0},{96,0,0},{79.999f,0,0},{95.999f,0,0},{0,80,0},{0,96,0},{-32.125f,40.5f,-3.25f}};
 constexpr float values[]={0,.024f,.025f,.25f,.75f,1};
 enemies.manager_flags=variant==9?1:0;
 for(u32 slot=0;slot<2;++slot){auto& boss=bosses[slot];boss={};boss.health=variant==4?100000:50;boss.max_health=100;boss.flags=variant==5?0x10:variant==6?0x21:0;boss.damage_immunity.current=variant==7?1:0;
 boss.current.position={float(positions[position].x+slot*13.f),float(positions[position].y-slot*7.f),positions[position].z};
 if(variant!=0&&(variant!=2||slot==1)&&(variant!=3||slot==0))enemies.bosses[slot]=&boss;
 auto& row=hud->th14_boss[slot];row.displayed=values[displayed];row.target=.75f;row.health=77;row.active=prior;row.hidden=hidden;
 constexpr float marks[]={0,.125f,.25f,.5f};for(u32 n=0;n<4;++n)enemies.th14_health_segments[slot][n]={marks[n],i32(9+n)};
 for(u32 n=0;n<7;++n){auto* vm=manager.create(front,0,5,u32(-1));if(!vm)return 0;old[slot][n]=vm->id;vm->pending_interrupt=0;row.handles[n]=prior?vm->id:0;}}
 auto* vm=manager.create(front,153,5,u32(-1));if(!vm)return 0;name_old=hud->boss_name=vm->id;
 first=anm_creation_count();HudInput input;input.stage=1;input.section=5;input.dialogue=variant==8;input.player_position={};
 if(!hud->bosses_th14(input))return 0;created.clear();for(u32 n=first;n<anm_creation_count();++n)created.push_back(anm_creation_value(n,0));return 1;
}
API(count) u32 count(){return created.size();} API(script) i32 script(u32 n){return created[n];}
API(state) u32 state(u32 slot,u32 k){auto& row=hud->th14_boss[slot];switch(k){case 0:return float_bits(row.displayed);case 1:return float_bits(row.target);case 2:return row.health;case 3:return row.active;case 4:return row.hidden;default:return 0;}}
API(mark) u32 mark(u32 slot,u32 n){return float_bits(enemies.th14_health_segments[slot][n].fraction);}
API(present) u32 present(u32 slot,u32 n){return bool(hud->th14_boss[slot].handles[n]);}
API(value) u32 value(u32 slot,u32 n,u32 k){auto* vm=manager.find(hud->th14_boss[slot].handles[n]);if(!vm)return u32(-1);switch(k){case 0:return vm->flags&6;case 1:return float_bits(vm->rotation.x);case 2:return float_bits(vm->rotation.z);case 3:return float_bits(vm->position.x);case 4:return float_bits(vm->position.y);case 5:return float_bits(vm->position.z);case 6:return vm->pending_interrupt;default:return 0;}}
API(retired) u32 retired(u32 slot,u32 n){auto* vm=manager.find(old[slot][n]);return vm&&bool(vm->flags&0x4000000);}
API(name_value) u32 name_value(u32 n){return n?bool(manager.find(name_old)->flags&0x4000000):bool(hud->boss_name);}
