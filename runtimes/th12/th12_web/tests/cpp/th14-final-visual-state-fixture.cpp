#include "../../cpp/game/Hud.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;
API(secondary) u32 secondary(i32 op,u32 flags,i32 duration,i32 mode){
 alignas(4) u8 bytes[40]{};auto* command=reinterpret_cast<AnmInstruction*>(bytes);command->opcode=i16(anm_canonical_opcode(op));command->length=op==413?28:20;const i32 args[]={duration,mode,op==413?23:123,67,89};std::memcpy(bytes+8,args,command->length-8);auto* stop=reinterpret_cast<AnmInstruction*>(bytes+command->length);*stop={2,8,0,0};
 AnmVm vm;vm.initialize();vm.th13_native_flags=flags;vm.color=0xc0123456;vm.secondary_color=0x9a6587ab;vm.script_begin=vm.instruction=command;vm.timer.set(0,&manager.rate);if(vm.update(manager))return ~0u;return vm.th13_native_flags;
}
API(hud_layer) i32 hud_layer(u32 layer){
 AnmResource front,ascii;for(auto* file:{&front,&ascii}){file->scripts.resize(100);file->templates=std::make_shared<AnmTemplatesTh14>();file->templates->scripts.resize(100);for(u32 i=0;i<100;++i){file->scripts[i].bytes={2,0,8,0,0,0,0,0};auto& vm=file->templates->scripts[i];vm.initialize();vm.layer=layer;vm.script_index=i;vm.resource=file;vm.script_begin=vm.instruction=reinterpret_cast<AnmInstruction*>(file->scripts[i].bytes.data());}}
 GameEconomy economy;EnemyCommandEnvironment enemies;StageCompletionState completion;HudEffects effects;i32 result=-1;
 {Hud hud(manager,front,ascii,economy,enemies,completion,effects);if(hud.notice(1,0))if(auto* vm=manager.find(hud.spell_time_animation))result=i32(vm->layer);}
 manager.clear();return result;
}
