#include "../../cpp/game/PauseMenu.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include "../../cpp/game/EclContext.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;
static AnmResource text,front;
static ScoreFile scores;
static std::unique_ptr<PauseMenu> menu;
static u32 first_creation;
static void append(AnmResource& file,u32 script,i16 op,const void* args=nullptr,u32 n=0){
    auto& b=file.scripts[script].bytes;const auto at=b.size();b.resize(at+8+n);
    const AnmInstruction h{op<0?op:i16(anm_canonical_opcode(op)),u16(8+n),0,0};std::memcpy(b.data()+at,&h,8);if(n)std::memcpy(b.data()+at+8,args,n);
}
API(run) i32 run(i32 script,u32 program){
    manager.clear();text={};front={};text.scripts.resize(53);front.scripts.resize(131);first_creation=anm_creation_count();
    for(const i32 index:{52,129,130}){
        auto& file=index==52?text:front;const i32 layer=index==52?35:28;append(file,index,304,&layer,4);
        if(program){const float p[]={3.25f,-7.5f,9.125f};append(file,index,400,p,12);}
        if(program==2){const i32 value=1;append(file,index,305,&value,4);}
        append(file,index,2);append(file,index,-1);
    }
    menu=std::make_unique<PauseMenu>(manager,text,front,scores);
    return script==52?menu->begin_end():menu->begin(script==130);
}
API(binding_count) u32 binding_count(){return anm_creation_count()-first_creation;}
API(binding) i32 binding(u32 n){return anm_creation_value(first_creation+n,0);}
API(sound_count) u32 sound_count(){return menu->sounds.size();}
API(sound) i32 sound(u32 n){return menu->sounds[n];}
API(capture) i32 capture(){return menu->capture_requested;}
API(value) u32 value(i32 script,u32 n){
    const auto* v=manager.find(script==52?menu->background_animation:menu->menu_animation);if(!v)return 0;
    const u32 words[]={v->layer,v->flags2&0x66220,float_bits(v->position.x),float_bits(v->position.y),float_bits(v->position.z),
        float_bits(v->script_position.x),float_bits(v->script_position.y),float_bits(v->script_position.z),float_bits(v->rotation.z)};return words[n];
}
