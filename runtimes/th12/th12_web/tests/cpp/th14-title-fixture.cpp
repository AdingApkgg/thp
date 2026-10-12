#include "../../cpp/game/TitleMenu.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmResource resources[3];
struct Fixture {
    AnmManager manager;ScoreFile scores;
    TitleMenu menu{manager,resources[0],resources[1],resources[2],scores};
    Fixture(){scores.settings.fill(0);manager.fallback_sprites=&resources[2];}
};
static Fixture* f=nullptr;
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(open_resource) int open_resource(u32 kind,const u8* p,u32 n){return kind<3&&resources[kind].open(p,n);}
API(reset) void reset(){delete f;f=new Fixture;}
API(tick) int tick(u32 pressed,u32 repeat){return f->menu.update(pressed,repeat)&&f->manager.update(false);}
API(main_case) int main_case(i32 unlocked,i32 selected,i32 substate,i32 timer,u32 pressed,u32 repeat){
    reset();auto& m=f->menu;if(unlocked)f->scores.characters[0][0x7dc]=1;
    m.cursor.count=10;m.cursor.select(selected);if(!unlocked){m.cursor.disabled_count=1;m.cursor.disabled[0]=1;}
    m.substate=substate;m.timer.set(timer,&f->manager.rate);return m.update(pressed,repeat);
}
API(selection_case) int selection_case(i32 kind,i32 difficulty,i32 character,i32 selected,i32 substate,i32 timer,u32 pressed,u32 repeat){
    reset();auto& m=f->menu;m.screen=TitleScreen(kind);m.selection.difficulty=m.selection.last_difficulty=difficulty;m.selection.character=character;
    m.cursor.count=kind==5?(difficulty==4?1:4):kind==6?3:2;m.cursor.wrap=kind!=5;m.cursor.select(selected);
    m.cursor.depth=1;m.cursor.selections[0]=0;m.cursor.counts[0]=10;m.substate=substate;m.timer.set(timer,&f->manager.rate);
    return m.update(pressed,repeat);
}
API(state) i32 state(u32 k){const auto& m=f->menu;switch(k){
    case 0:return i32(m.screen);case 1:return m.substate;case 2:return m.cursor.selected;case 3:return m.cursor.count;
    case 4:return m.sounds.size();case 5:return m.selection.difficulty;case 6:return m.selection.flags;
    case 7:return m.start_requested;case 8:return m.selection.stage;case 9:return m.timer.current;
    case 10:return m.selection.character;case 11:return m.selection.partner;
    default:return m.fade_requested;
}}
API(sound) i32 sound(u32 i){return f->menu.sounds.at(i);}
API(script_in_slot) i32 script_in_slot(u32 slot){auto* vm=f->manager.find(f->menu.handles.at(slot));return vm?vm->script_index:-1;}
API(error) const char* error(){return f->menu.error.c_str();}
