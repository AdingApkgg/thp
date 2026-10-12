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
static std::vector<u32> created;
static void stopped(AnmResource& f,u32 script){const AnmInstruction code[]={{i16(anm_canonical_opcode(2)),8,0,0},{-1,8,0,0}};auto& b=f.scripts[script].bytes;b.resize(sizeof code);std::memcpy(b.data(),code,sizeof code);}
API(run) u32 run(i32 stage,i32 character,i32 replay,i32 continues,i32 demo,i32 prior,i32 base_prior){
    hud.reset();manager.clear();front={};text={};logo={};economy={};enemies={};completion={};front.scripts.resize(120);text.scripts.resize(4);
    logo.scripts.resize(2);for(u32 i=0;i<2;++i)stopped(logo,i);
    for(u32 i=0;i<120;++i)stopped(front,i);for(u32 i=0;i<4;++i)stopped(text,i);
    hud=std::make_unique<Hud>(manager,front,text,economy,enemies,completion,effects);
    if(prior){auto* vm=manager.create(front,111,5,u32(-1));if(!vm)return 0;hud->th14_overlay=vm->id;}
    if(base_prior){auto* vm=manager.create(front,0,5,u32(-1));if(!vm)return 0;hud->frame_animation=vm->id;}
    const u32 first=anm_creation_count();HudInput input;input.stage=stage;input.character=character;
    if(!hud->start_stage(logo,input,demo,false,replay,continues))return 0;created.clear();
    for(u32 i=first;i<anm_creation_count();++i){const i32 script=anm_creation_value(i,0);if(anm_creation_value(i,2)==5&&(script==0||script==67||script==70||script==94||script==111))created.push_back(u32(anm_creation_value(i,5)));}
    return 1;
}
API(count) u32 count(){return created.size();}
API(value) u32 value(u32 n,u32 k){const auto* vm=manager.find(created[n]);if(!vm)return u32(-1);switch(k){case 0:return vm->script_index;case 1:return vm->flags2&0x200;case 2:return float_bits(vm->position.x);case 3:return float_bits(vm->position.y);case 4:return float_bits(vm->position.z);case 5:return float_bits(vm->rotation.z);default:return 0;}}
API(retained) u32 retained(u32 which){return which?!!hud->th14_overlay:!!hud->frame_animation;}
API(logo_run) u32 logo_run(i32 mode,u32 flags){
    if(!run(1,0,0,0,0,0,0))return 0;
    enemies.th14_runtime_mode=mode;enemies.th14_run_flags=flags;created.clear();const u32 first=anm_creation_count();HudInput input;
    if(!hud->start_stage(logo,input,(flags&0x40)!=0,false,0,0))return 0;
    for(u32 i=first;i<anm_creation_count();++i)if(anm_creation_value(i,2)==6)created.push_back(u32(anm_creation_value(i,5)));
    return 1;
}
