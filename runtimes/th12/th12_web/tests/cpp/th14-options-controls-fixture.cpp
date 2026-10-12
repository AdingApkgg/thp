#include "../../cpp/game/TitleMenu.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(n) extern "C" __attribute__((export_name(#n)))
static AnmManager manager;static AnmResource title,variant,ascii;static ScoreFile scores;static std::unique_ptr<TitleMenu> menu;
API(run) i32 run(i32 state,i32 timer,i32 previous,i32 selected,u32 pressed,u32 repeat,u32 bgm,u32 sound,u32 focus){
 manager.clear();title={};title.scripts.resize(2);AnmInstruction h{i16(anm_canonical_opcode(2)),8,0,0};for(auto& s:title.scripts){s.bytes.resize(8);std::memcpy(s.bytes.data(),&h,8);}
 menu=std::make_unique<TitleMenu>(manager,title,variant,ascii,scores);menu->screen=TitleScreen::Options;menu->substate=state;
 menu->cursor.count=10;menu->cursor.select(7);menu->cursor.push();menu->cursor.count=5;menu->cursor.select(selected);
 menu->timer.set(timer,&manager.rate);menu->timer.previous=previous;menu->config.bytes[0x22]=bgm;menu->config.bytes[0x23]=sound;menu->config.bytes[0x24]=focus;
 if(state!=0){auto* vm=manager.create(title,1,24,22);if(!vm)return 0;menu->handles[1]=vm->id;vm->pending_interrupt=0;}
 return menu->update(pressed,repeat);
}
API(value) i32 value(u32 n){switch(n){case 0:return i32(menu->screen);case 1:return menu->substate;case 2:return menu->cursor.selected;case 3:return menu->cursor.count;case 4:return menu->cursor.depth;case 5:return menu->volume_changed;case 6:return menu->sounds.size();case 7:{auto* vm=manager.find(menu->handles[1]);return vm?vm->pending_interrupt:0;}default:return -999;}}
API(sound) i32 sound(u32 n){return menu->sounds[n];}
API(config) i32 config(u32 n){return menu->config.bytes[0x22+n];}
