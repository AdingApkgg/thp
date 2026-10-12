#include "../../cpp/game/PauseMenu.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include "../../cpp/game/EclContext.hpp"
#include <memory>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;
static AnmResource text,front;
static ScoreFile scores;
static std::unique_ptr<PauseMenu> menu;
static u32 creation;
static void script(AnmResource& file,i32 index){
    auto& bytes=file.scripts[index].bytes;bytes.resize(16);const AnmInstruction a{i16(anm_canonical_opcode(3)),8,0,0},b{-1,8,0,0};std::memcpy(bytes.data(),&a,8);std::memcpy(bytes.data()+8,&b,8);
}
API(run) i32 run(i32 phase,i32 substate,i32 timer,i32 selected,u32 pressed,u32 repeat,i32 origin){
    manager.clear();menu=std::make_unique<PauseMenu>(manager,text,front,scores);menu->manual_resource=std::make_unique<AnmResource>();menu->manual_resource->scripts.resize(10);
    for(i32 i=0;i<10;++i){script(*menu->manual_resource,i);auto* vm=manager.create(*menu->manual_resource,i,19,0,true);menu->manual_animations[i]=vm->id;}
    menu->state=15;menu->manual_phase=phase;menu->manual_substate=substate;menu->manual_timer.set(timer,&manager.rate);
    menu->manual_origin_x=float(origin);
    menu->manual_cursor.count=7;menu->manual_cursor.wrap=1;menu->manual_cursor.selected=selected;creation=anm_creation_count();
    return menu->update(pressed,repeat);
}
API(value) i32 value(u32 n){const i32 words[]={menu->manual_phase,menu->manual_substate,menu->manual_timer.current,menu->manual_cursor.selected,i32(menu->manual_finished),menu->manual_image_requested};return words[n];}
API(binding_count) u32 binding_count(){return anm_creation_count()-creation;}
API(binding) i32 binding(u32 i){return anm_creation_value(creation+i,0);}
API(position) u32 position(u32 i,u32 n){const auto* vm=manager.find(u32(anm_creation_value(creation+i,5)));return vm?float_bits(n==0?vm->position.x:n==1?vm->position.y:vm->position.z):u32(-1);}
API(sound_count) u32 sound_count(){return menu->sounds.size();}
API(sound) i32 sound(u32 i){return menu->sounds[i];}
API(label) i32 label(u32 i){const auto* vm=manager.find(menu->manual_animations[i]);return vm?vm->pending_interrupt:0;}
