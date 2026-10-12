#include "../../cpp/game/TitleMenu.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include "../../cpp/game/EclContext.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;
static AnmResource title,variant,ascii;
static ScoreFile scores;
static std::unique_ptr<TitleMenu> menu;
static u32 first,old_ascii,old_title;
static std::vector<u32> created;
static void stopped(AnmResource& f,u32 script){const AnmInstruction code[]={{i16(anm_canonical_opcode(2)),8,0,0},{-1,8,0,0}};auto& b=f.scripts[script].bytes;b.resize(sizeof code);std::memcpy(b.data(),code,sizeof code);}
API(run) u32 run(i32 substate,i32 timer,i32 ascii_present,i32 finished){
    menu.reset();manager.clear();title={};variant={};ascii={};title.scripts.resize(104);ascii.scripts.resize(20);
    for(u32 i=0;i<104;++i)stopped(title,i);for(u32 i=0;i<20;++i)stopped(ascii,i);
    menu=std::make_unique<TitleMenu>(manager,title,variant,ascii,scores);menu->flags=0;menu->screen=TitleScreen::Manual;menu->substate=substate;menu->timer.set(timer,&manager.rate);menu->manual_finished=finished;
    old_title=manager.create(title,103,24,u32(-1))->id;menu->handles[103]=old_title;old_ascii=0;
    if(ascii_present){old_ascii=manager.create(ascii,19,2,u32(-1))->id;menu->handles[261]=old_ascii;}
    first=anm_creation_count();if(!menu->update(0,0))return 0;created.clear();
    for(u32 i=first;i<anm_creation_count();++i)if(!anm_creation_value(i,4))created.push_back(i);return 1;
}
API(value) u32 value(u32 n){switch(n){case 0:return u32(menu->screen);case 1:return menu->substate;case 2:return menu->timer.current;case 3:return !!menu->handles[261];case 4:return !!menu->handles[103];case 5:return menu->manual_requested;case 6:return menu->manual_release_requested;case 7:return float_bits(menu->manual_origin_x);default:return 0;}}
API(count) u32 count(){return created.size();}
API(binding) u32 binding(u32 i,u32 k){return u32(anm_creation_value(created[i],k?0:2));}
API(label) u32 label(u32 n){const auto* vm=manager.find(n?old_title:old_ascii);return vm?u32(vm->pending_interrupt):0;}
