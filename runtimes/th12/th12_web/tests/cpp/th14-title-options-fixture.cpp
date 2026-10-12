#include "../../cpp/game/TitleMenu.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager animations;
static AnmResource title,variant,ascii;
static ScoreFile scores;
static std::unique_ptr<TitleMenu> menu;
static std::array<i32,10> labels{};
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(open) u32 open(const u8* p,u32 n){return title.open(p,n);}
API(open_ascii) u32 open_ascii(const u8* p,u32 n){return ascii.open(p,n);}
API(error) const char* error(){return menu?menu->error.c_str():"not initialized";}
static AnmVm* child(i32 script){
 auto* parent=animations.find(menu->handles[1]);if(!parent)return nullptr;
 for(auto* node=&parent->child;node;node=node->next)if(node->value->script_index==script)return node->value;
 return nullptr;
}
API(run) u32 run(u32 bgm,u32 sound){
 animations.clear();animations.fallback_sprites=&ascii;menu=std::make_unique<TitleMenu>(animations,title,variant,ascii,scores);
 menu->change(TitleScreen::Options);menu->config.bytes[0x22]=u8(bgm);menu->config.bytes[0x23]=u8(sound);
 if(!menu->update(0,0))return 0;
 return 1;
}
API(value) i32 value(u32 script,u32 kind){
 auto* vm=child(i32(script));if(!vm)return -999;
 if(kind==0)return vm->sprite_index;
 return bool(vm->flags&2);
}
API(change_volume) u32 change_volume(u32 channel,u32 pressed){
 menu->substate=2;menu->cursor.select(i32(channel));menu->timer.set(20,&animations.rate);
 menu->update(pressed,0);return menu->config.bytes[0x22+channel];
}
API(set_clear) void set_clear(i32 selection,u32 difficulty,u32 flag,u32 legacy_preferences){
 scores.characters={};scores.settings={};
 if(selection>=0&&selection<7)std::memcpy(scores.characters[selection].data()+0x7dc+difficulty*4,&flag,4);
 if(legacy_preferences)std::memset(scores.settings.data()+0x1c,0x10,6);
}
API(available) u32 available(u32 selection){return menu->available(i32(selection/2),i32(selection%2));}
API(unlocked) u32 unlocked(){return menu->unlocked();}
