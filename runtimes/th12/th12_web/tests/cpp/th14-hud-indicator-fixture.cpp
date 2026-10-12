#include "../../cpp/game/Hud.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include "../../cpp/game/EclContext.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;static AnmResource front,text;static GameEconomy economy;static EnemyCommandEnvironment enemies;
static StageCompletionState completion;static HudEffects effects;static std::unique_ptr<Hud> hud;static EnemyState boss;static AnmVm children[2];static u32 handle;
API(run) u32 run(i32 present,u32 flags,u32 mode,i32 spell,i32 value,float x,float px,i32 child_mode){
 hud.reset();manager.clear();front={};enemies={};front.scripts.resize(112);
 const AnmInstruction code[]={{i16(anm_canonical_opcode(2)),8,0,0},{-1,8,0,0}};
 for(auto& s:front.scripts){s.bytes.resize(sizeof code);std::memcpy(s.bytes.data(),code,sizeof code);}
 hud=std::make_unique<Hud>(manager,front,text,economy,enemies,completion,effects);auto* vm=manager.create(front,111,5,u32(-1));if(!vm)return 0;handle=hud->th14_overlay=vm->id;
 vm->color=0xc0123456;vm->pending_interrupt=17;vm->position={23,31,0};
 for(auto& child:children){child.initialize();child.child.value=&child;}if(child_mode){vm->child.next=&children[0].child;children[0].child.next=&children[1].child;}if(child_mode==2)vm->child.previous=&children[1].child;
 boss={};boss.flags=flags;boss.interrupt_health=value;boss.current.position.x=x;if(present)enemies.bosses[0]=&boss;completion.hud_flags=0xa500|mode*2;
 HudInput input;input.spell=spell;input.player_position.x=px;return hud->indicator_th14(input)?1:0;
}
API(value) u32 value(u32 k){auto* vm=manager.find(handle);switch(k){case 0:return completion.hud_flags;case 1:return vm->flags&2;case 2:return vm->color;case 3:return vm->pending_interrupt;case 4:return float_bits(vm->position.x);case 5:return float_bits(vm->position.y);default:return bool(children[k-6].flags&2);}}
