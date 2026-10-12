#include "../../cpp/game/Hud.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include "../../cpp/game/EclContext.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;static AnmResource front,text;static GameEconomy economy;
static EnemyCommandEnvironment enemies;static StageCompletionState completion;static HudEffects effects;
static std::unique_ptr<Hud> hud;static std::vector<u32> created;static u32 old[10]{};
static void reset(){hud.reset();manager.clear();front={};enemies={};front.scripts.resize(256);
 const AnmInstruction code[]={{i16(anm_canonical_opcode(2)),8,0,0},{-1,8,0,0}};
 for(auto& s:front.scripts){s.bytes.resize(sizeof code);std::memcpy(s.bytes.data(),code,sizeof code);}
 hud=std::make_unique<Hud>(manager,front,text,economy,enemies,completion,effects);created.clear();}
static void collect(u32 first){for(u32 n=first;n<anm_creation_count();++n)created.push_back(n);}
API(name_run) u32 name_run(i32 stage,i32 section,i32 spell,i32 subtype,i32 prior){
 reset();if(prior==1){auto* vm=manager.create(front,0,5,u32(-1));if(!vm)return 0;hud->boss_name=vm->id;}else if(prior==2)hud->boss_name=0x7fffffff;
 const u32 first=anm_creation_count();HudInput input;input.stage=stage;input.section=section;input.spell_id=spell;input.subtype=subtype;
 if(!hud->boss_name_th14(input))return 0;collect(first);return 1;
}
API(mark_run) u32 mark_run(i32 remaining,i32 pattern){
 reset();for(u32 n=0;n<10;++n){auto* vm=manager.create(front,0,5,u32(-1));if(!vm)return 0;old[n]=vm->id;vm->pending_interrupt=0;
 hud->stars[n]=pattern==3?0x7ffff000+n:(pattern==1||(pattern==2&&n%2==0)?vm->id:0);}
 const u32 first=anm_creation_count();enemies.remaining_phases=remaining;if(!hud->remaining_th14())return 0;collect(first);return 1;
}
API(count) u32 count(){return created.size();}
API(value) u32 value(u32 n,u32 k){const auto* vm=manager.find(u32(anm_creation_value(created[n],5)));if(!vm)return u32(-1);switch(k){case 0:return vm->script_index;case 1:return vm->flags2&0x200;case 2:return float_bits(vm->position.x);case 3:return float_bits(vm->position.y);case 4:return float_bits(vm->position.z);case 5:return float_bits(vm->rotation.z);default:return 0;}}
API(retained) u32 retained(){return bool(hud->boss_name);}
API(mark) u32 mark(u32 n){return bool(hud->stars[n]);}
API(pending) u32 pending(u32 n){auto* vm=manager.find(old[n]);return vm?vm->pending_interrupt:0;}
