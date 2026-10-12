#include "../../cpp/game/Hud.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include "../../cpp/game/EclContext.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;
static AnmResource front,text,logo;
static GameEconomy economy;
static EnemyCommandEnvironment enemies;
static StageCompletionState completion;
static HudEffects effects;
static std::unique_ptr<Hud> hud;
static u32 old_handle,first;
static std::vector<u32> created;
static void stopped(AnmResource& f,u32 script){const AnmInstruction code[]={{i16(anm_canonical_opcode(2)),8,0,0},{-1,8,0,0}};auto& b=f.scripts[script].bytes;b.resize(sizeof code);std::memcpy(b.data(),code,sizeof code);}
API(run) u32 run(i32 difficulty,i32 initial,i32 prior,i32 pending){
    hud.reset();manager.clear();front={};text={};logo={};economy={};front.scripts.resize(120);text.scripts.resize(4);
    logo.scripts.resize(2);for(u32 i=0;i<2;++i)stopped(logo,i);
    for(u32 i=0;i<120;++i)stopped(front,i);for(u32 i=0;i<4;++i)stopped(text,i);hud=std::make_unique<Hud>(manager,front,text,economy,enemies,completion,effects);old_handle=0;
    if(prior){auto* old=manager.create(front,79,5,u32(-1));if(!old)return 0;old_handle=old->id;old->pending_interrupt=pending;hud->difficulty_intro=old_handle;}
    economy.difficulty=difficulty;first=anm_creation_count();HudInput input;input.stage=2;
    if(!hud->start_stage(logo,input,false,initial,0,0))return 0;created.clear();
    for(u32 i=first;i<anm_creation_count();++i){const i32 script=anm_creation_value(i,0);if(anm_creation_value(i,2)==5&&((script>=57&&script<=66)||(script>=79&&script<=89)))created.push_back(i);}
    return 1;
}
API(count) u32 count(){return created.size();}
API(value) u32 value(u32 n,u32 k){const u32 record=created[n];const auto* vm=manager.find(u32(anm_creation_value(record,5)));if(!vm)return u32(-1);switch(k){case 0:return vm->script_index;case 1:return vm->flags2&0x200;case 2:return float_bits(vm->position.x);case 3:return float_bits(vm->position.y);case 4:return float_bits(vm->position.z);case 5:return float_bits(vm->rotation.z);case 6:return vm->pending_interrupt;default:return 0;}}
API(old_pending) u32 old_pending(){auto* vm=manager.find(old_handle);return vm?u32(vm->pending_interrupt):0;}
