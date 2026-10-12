#include "../../cpp/game/PauseMenu.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(n) extern "C" __attribute__((export_name(#n)))
static AnmManager manager;static AnmResource text,front;static ScoreFile scores;
static std::unique_ptr<PauseMenu> menu;static std::array<AnmVm*,12> children;
static constexpr i32 scripts[]={118,119,120,127,128,151,78,79,80,87,88,152};
API(run) i32 run(i32 state,i32 timer,i32 selected,u32 pressed,i32 replay,i32 continues){
 manager.clear();text={};front={};text.scripts.resize(53);front.scripts.resize(153);
 auto script=[](AnmResource& f,i32 i){AnmInstruction h{i16(anm_canonical_opcode(2)),8,0,0};f.scripts[i].bytes.resize(8);std::memcpy(f.scripts[i].bytes.data(),&h,8);};
 script(text,52);for(i32 i=0;i<153;++i)script(front,i);
 menu=std::make_unique<PauseMenu>(manager,text,front,scores);if(!menu->begin(replay))return 0;
 auto* root=manager.find(menu->menu_animation);root->pending_interrupt=0;AnmVm::Node* tail=&root->child;
 for(u32 n=0;n<children.size();++n){auto* child=manager.create(front,scripts[n],5,0,true);if(!child)return 0;children[n]=child;child->child.previous=tail;tail->next=&child->child;tail=&child->child;child->pending_interrupt=0;}
 menu->state=state;menu->timer.set(timer,&manager.rate);menu->cursor={};menu->cursor.count=state==5||state==7?2:5;menu->cursor.wrap=1;menu->cursor.selected=selected;menu->continues=continues;
 return menu->update(pressed,0);
}
API(value) i32 value(u32 n){switch(n){case 0:return menu->state;case 1:return menu->cursor.selected;case 2:return menu->cursor.count;case 3:return menu->cursor.wrap;case 4:return menu->cursor.disabled_count;case 5:return manager.find(menu->menu_animation)->pending_interrupt;case 6:return menu->manual_requested;case 7:return menu->sounds.size();default:return -1;}}
API(disabled) i32 disabled(u32 n){return menu->cursor.disabled[n];}
API(sound) i32 sound(u32 n){return menu->sounds[n];}
API(child) i32 child(u32 n){return children[n]->pending_interrupt;}
