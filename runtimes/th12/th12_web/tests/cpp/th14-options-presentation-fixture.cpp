#include "../../cpp/game/TitleMenu.hpp"
using namespace th11;
#define API(n) extern "C" __attribute__((export_name(#n)))
static AnmManager manager;static AnmResource title,variant,ascii;static ScoreFile scores;static std::unique_ptr<TitleMenu> menu;
API(run) u32 run(i32 selected,u32 cancel){
 manager.clear();title={};title.scripts.resize(49);
 for(auto& s:title.scripts){
  auto add=[&](i16 op,u16 refs,std::initializer_list<i32> args){AnmInstruction h{op,u16(8+args.size()*4),0,refs};const auto offset=s.bytes.size();s.bytes.resize(offset+h.length);std::memcpy(s.bytes.data()+offset,&h,8);std::memcpy(s.bytes.data()+offset+8,args.begin(),args.size()*4);};
  add(63,0,{});for(const i32 label:{30,31}){add(64,0,{label});add(6,1,{10000,label});add(63,0,{});}add(-1,0,{});
 }
 menu=std::make_unique<TitleMenu>(manager,title,variant,ascii,scores);menu->screen=TitleScreen::Options;menu->substate=cancel?2:1;menu->cursor.count=5;menu->cursor.select(selected);menu->timer.set(7,&manager.rate);
 auto* root=manager.create(title,1,24,22);if(!root)return 0;menu->handles[1]=root->id;
 auto* tail=&root->child;for(i32 script=23;script<=48;++script){auto* vm=manager.spawn(*root,script,90);if(!vm)return 0;tail->next=&vm->child;vm->child.previous=tail;tail=&vm->child;}
 return menu->update(cancel?2:0,0);
}
API(value) i32 value(u32 script){auto* root=manager.find(menu->handles[1]);if(root)for(auto* n=&root->child;n;n=n->next)if(n->value->script_index==i32(script))return n->value->integers[0];return -999;}
