#include "../../cpp/game/SpellTh14Visuals.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;static AnmResource ascii,text,effect;static EnemyAnimations files(manager);static u32 titles[3],circle,background;
static void resource(AnmResource& file,u32 count,u32 layer){
 file.scripts.resize(count);file.templates=std::make_shared<AnmTemplatesTh14>();file.templates->scripts.resize(count);
 for(u32 i=0;i<count;++i){file.scripts[i].bytes={2,0,8,0,0,0,0,0};auto& vm=file.templates->scripts[i];vm.initialize();vm.layer=layer;vm.script_index=i;vm.resource=&file;vm.script_begin=vm.instruction=reinterpret_cast<AnmInstruction*>(file.scripts[i].bytes.data());}
}
API(run) i32 run(u32 layer){
 manager.clear();resource(ascii,2,layer);resource(text,3,layer);resource(effect,14,layer);files.resources={};files.resources[3]={&effect,3};
 // The title phase is complete before the deliberately absent circle children
 // make the later phase return false. This fixture checks title construction.
 const bool result=spell_th14_create_visuals(manager,files,ascii,text,effect,7,7,0,2400,{0,100,0},titles,circle,background,[](u32){return true;},[](i32){return true;});return result?1:0;
}
API(layer) u32 layer(u32 slot){auto* vm=slot<3?manager.find(titles[slot]):nullptr;return vm?vm->layer:0xffffffff;}
