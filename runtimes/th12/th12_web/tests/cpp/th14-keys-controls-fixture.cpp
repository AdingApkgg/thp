#include "../../cpp/game/TitleMenu.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(n) extern "C" __attribute__((export_name(#n)))
static AnmManager manager;static AnmResource title,variant,ascii;static ScoreFile scores;static std::unique_ptr<TitleMenu> menu;
static std::array<i16,6> edited;static std::array<i16,10> config;
API(set) void set(u32 kind,u32 index,i32 value){if(kind)config[index]=i16(value);else edited[index]=i16(value);}
API(run) i32 run(i32 state,i32 timer,i32 previous,i32 selected,u32 pressed,u32 repeat,u32 buttons){
 manager.clear();title={};title.scripts.resize(3);AnmInstruction h{i16(anm_canonical_opcode(2)),8,0,0};for(auto& s:title.scripts){s.bytes.resize(8);std::memcpy(s.bytes.data(),&h,8);}
 menu=std::make_unique<TitleMenu>(manager,title,variant,ascii,scores);menu->screen=TitleScreen::Keys;menu->substate=state;
 menu->cursor.count=5;menu->cursor.select(2);menu->cursor.push();menu->cursor.count=6;menu->cursor.select(selected);
 menu->timer.set(timer,&manager.rate);menu->timer.previous=previous;menu->controller_buttons=buttons;
 std::memcpy(menu->config.bytes.data()+4,config.data(),20);
 for(u32 i=0;i<menu->edited_buttons.size();++i)menu->edited_buttons[i]=edited[i];
 if(state!=0){auto* vm=manager.create(title,2,24,22);if(!vm)return 0;menu->handles[2]=vm->id;vm->pending_interrupt=0;}
 return menu->update(pressed,repeat);
}
API(value) i32 value(u32 n){switch(n){case 0:return i32(menu->screen);case 1:return menu->substate;case 2:return menu->cursor.selected;case 3:return menu->cursor.count;case 4:return menu->cursor.depth;case 5:return menu->sounds.size();case 6:{auto* vm=manager.find(menu->handles[2]);return vm?vm->pending_interrupt:0;}default:return -999;}}
API(sound) i32 sound(u32 n){return menu->sounds[n];}
API(binding) i32 binding(u32 kind,u32 n){if(kind){i16 v;std::memcpy(&v,menu->config.bytes.data()+4+n*2,2);return v;}return n<menu->edited_buttons.size()?menu->edited_buttons[n]:edited[n];}
