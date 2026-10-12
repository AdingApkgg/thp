#include "../../cpp/game/TitleMenu.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmResource resources[3];
struct Fixture {
    AnmManager manager;ScoreFile scores;
    TitleMenu menu{manager,resources[0],resources[1],resources[2],scores};
    Fixture(){scores.settings.fill(0);for(int i=0;i<8;++i)scores.settings[0x1c+i]=16;}
};
static Fixture* f=nullptr;
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(open_resource) int open_resource(u32 kind,const u8* p,u32 n){return kind<3&&resources[kind].open(p,n);}
API(reset) void reset(){delete f;f=new Fixture;}
API(tick) int tick(u32 pressed,u32 repeat){return f->menu.update(pressed,repeat)&&f->manager.update(false);}
API(character_case) int character_case(i32 difficulty,i32 selected,u32 pressed,u32 repeat){
    reset();auto& m=f->menu;m.change(TitleScreen::Character);m.selection.difficulty=difficulty;m.cursor.select(selected);
    for(int i=0;i<9;++i)if(!tick(0,0))return 0;
    return tick(pressed,repeat);
}
API(state) i32 state(u32 k){const auto& m=f->menu;switch(k){
    case 0:return i32(m.screen);case 1:return m.substate;case 2:return m.cursor.selected;case 3:return m.cursor.count;
    case 4:return m.sounds.size();case 5:return m.selection.character;case 6:return m.selection.partner;
    case 7:return m.start_requested;case 8:return m.selection.stage;case 9:return m.timer.current;
    default:return m.fade_requested;
}}
API(sound) i32 sound(u32 i){return f->menu.sounds.at(i);}
API(script_in_slot) i32 script_in_slot(u32 slot){auto* vm=f->manager.find(f->menu.handles.at(slot));return vm?vm->script_index:-1;}
API(error) const char* error(){return f->menu.error.c_str();}
