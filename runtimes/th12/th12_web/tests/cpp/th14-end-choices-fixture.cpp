#include "../../cpp/game/PauseMenu.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include <memory>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;
static AnmResource text,front;
static ScoreFile scores;
static std::unique_ptr<PauseMenu> menu;
static u32 creation;
static void script(AnmResource& file,i32 index,i32 layer){
    auto& bytes=file.scripts[index].bytes;bytes.resize(28);
    const AnmInstruction a{i16(anm_canonical_opcode(304)),12,0,0},b{i16(anm_canonical_opcode(3)),8,0,0},c{-1,8,0,0};
    std::memcpy(bytes.data(),&a,8);std::memcpy(bytes.data()+8,&layer,4);std::memcpy(bytes.data()+12,&b,8);std::memcpy(bytes.data()+20,&c,8);
}
API(run) i32 run(i32 difficulty,i32 continues,i32 selected,u32 pressed,u32 repeat){
    manager.clear();text={};front={};text.scripts.resize(53);front.scripts.resize(145);scores={};
    script(text,52,35);script(front,139,28);script(front,144,28);
    // Retail proof controls447e00's return to -1. Make the real unsigned
    // ScoreFile consumer produce that result instead of using signed -1,
    // which is a valid highest score in TH14.
    for(i32 rank=0;rank<10;++rank){const u32 score=1;std::memcpy(scores.characters[0].data()+0x10+(difficulty*10+rank)*28,&score,4);}
    menu=std::make_unique<PauseMenu>(manager,text,front,scores);menu->result_score=0;menu->difficulty=difficulty;menu->continues=continues;
    if(!menu->begin_end())return 0;menu->sounds.clear();creation=anm_creation_count();menu->timer.set(10,&manager.rate);
    if(!menu->update(0,0))return 0;
    if(selected>=0){menu->cursor.selected=selected;menu->update(pressed,repeat);}return menu->error.empty();
}
API(value) i32 value(u32 n){const i32 words[]={menu->cursor.selected,menu->cursor.previous,menu->cursor.count,menu->cursor.wrap,menu->cursor.disabled_count,menu->state};return words[n];}
API(disabled) i32 disabled(u32 n){return menu->cursor.disabled[n];}
API(binding) i32 binding(){return anm_creation_value(creation,0);}
API(sound_count) u32 sound_count(){return menu->sounds.size();}
API(sound) i32 sound(u32 n){return menu->sounds[n];}
