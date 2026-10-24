// Compile this diagnostic with -fno-access-control to observe the private
// production GameBattle::hud_input connection without changing its API.
#include "../../cpp/game/GameBattle.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static GameSessionResources resources;
static AnmManager animations;
static GameEconomy economy;
static SpellRecords records;
static SceneCompositor scene(animations);
static ClearRecords clears;
static std::unique_ptr<GameBattle> battle;
API(name_input_run) i32 name_input_run(i32 stage,i32 section,i32 practice,i32 subtype,i32 current){
    if(!battle){
        auto& front=resources.core.front;front.scripts.resize(256);
        const AnmInstruction code[]={{i16(anm_canonical_opcode(2)),8,0,0},{-1,8,0,0}};
        for(auto& s:front.scripts){s.bytes.resize(sizeof code);std::memcpy(s.bytes.data(),code,sizeof code);}
        battle=std::make_unique<GameBattle>(resources,animations,economy,records,scene,clears);
    }
    animations.clear();battle->hud.boss_name=0;
    resources.stage_number=u32(stage);battle->enemy_commands.stage_section=section;
    battle->enemy_environment.subtype=subtype;battle->enemy_environment.spell_practice_id=practice;
    battle->spell_id=current;
    if(!battle->hud.boss_name_th14(battle->hud_input()))return -2;
    const auto* vm=animations.find(battle->hud.boss_name);return vm?vm->script_index:-1;
}
