#include "../../cpp/game/TitleMenu.hpp"
#include <cstdlib>
using namespace th11;
#define API(n) extern "C" __attribute__((export_name(#n)))
static AnmManager manager;static AnmResource title,synthetic,variant,ascii;static ScoreFile scores;static std::unique_ptr<TitleMenu> menu;
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(open) u32 open(const u8* p,u32 n,u32 kind){return kind?ascii.open(p,n):title.open(p,n);}
static AnmVm* child(i32 script){auto* root=manager.find(menu->handles[2]);if(root)for(auto* n=&root->child;n;n=n->next)if(n->value->script_index==script)return n->value;return nullptr;}
API(run) u32 run(i32 a,i32 b,i32 c,i32 d){
 manager.clear();manager.fallback_sprites=&ascii;menu=std::make_unique<TitleMenu>(manager,title,variant,ascii,scores);menu->screen=TitleScreen::Keys;
 const i16 values[]={i16(a),i16(b),i16(c),i16(d)};std::memcpy(menu->config.bytes.data()+4,values,8);return menu->update(0,0);
}
API(value) i32 value(u32 script,u32 kind){auto* vm=child(script);return vm?(kind?vm->integers[0]:vm->sprite_index):-999;}
API(present) u32 present(i32 selected){
 manager.clear();synthetic={};synthetic.scripts.resize(77);
 for(auto& s:synthetic.scripts){
  auto add=[&](i16 op,u16 refs,std::initializer_list<i32> args){AnmInstruction h{op,u16(8+args.size()*4),0,refs};const auto offset=s.bytes.size();s.bytes.resize(offset+h.length);std::memcpy(s.bytes.data()+offset,&h,8);std::memcpy(s.bytes.data()+offset+8,args.begin(),args.size()*4);};
  add(63,0,{});for(const i32 label:{30,31}){add(64,0,{label});add(6,1,{10000,label});add(63,0,{});}add(-1,0,{});
 }
 menu=std::make_unique<TitleMenu>(manager,synthetic,variant,ascii,scores);menu->screen=TitleScreen::Keys;menu->substate=1;menu->cursor.count=6;menu->cursor.select(selected);menu->timer.set(7,&manager.rate);
 auto* root=manager.create(synthetic,2,24,22);if(!root)return 0;menu->handles[2]=root->id;
 auto* tail=&root->child;for(i32 script=49;script<=76;++script){auto* vm=manager.spawn(*root,script,90);if(!vm)return 0;tail->next=&vm->child;vm->child.previous=tail;tail=&vm->child;}
 return menu->update(0,0);
}
