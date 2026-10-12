#include "../../cpp/game/PauseMenu.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include "../../cpp/game/EclContext.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static std::unique_ptr<AnmManager> manager;static AnmResource text,front;static ScoreFile scores;static std::unique_ptr<PauseMenu> menu;static u32 first_creation;static AnmVm* vm;
static i32 initial_kind=0;
static AnmResource ascii_resource;static AsciiText ascii(ascii_resource);
static void setup(u32 program){
 menu.reset();manager=std::make_unique<AnmManager>();text={};front={};text.scripts.resize(53);front.scripts.resize(162);
 for(auto* file:{&text,&front})for(auto& script:file->scripts){
  if(program){const AnmInstruction ins{i16(anm_canonical_opcode(304)),12,0,0};const i32 layer=35;script.bytes.resize(12);std::memcpy(script.bytes.data(),&ins,8);std::memcpy(script.bytes.data()+8,&layer,4);}
  const AnmInstruction code[]={AnmInstruction{i16(anm_canonical_opcode(2)),8,0,0},AnmInstruction{-1,8,0,0}};const auto at=script.bytes.size();script.bytes.resize(at+16);std::memcpy(script.bytes.data()+at,code,16);
 }
 menu=std::make_unique<PauseMenu>(*manager,text,front,scores);first_creation=anm_creation_count();
}
API(entry) i32 entry(u32 kind){setup(0);return kind==2?menu->begin_end():menu->begin(kind==1);}
API(binding_count) u32 binding_count(){return anm_creation_count()-first_creation;}
API(binding) i32 binding(u32 n,u32 field){return anm_creation_value(first_creation+n,field==0?2:0);}
API(sound_count) u32 sound_count(){return menu->sounds.size();}
API(sound) i32 sound(u32 n){return menu->sounds[n];}
API(state_word) i32 state_word(u32 n){return n?menu->th16_substate:menu->state;}
API(capture) i32 capture(){return menu->capture_requested;}
API(factory) i32 factory(i32 script,u32 program){setup(program);vm=menu->th16_overlay(script==52?text:front,script,script==52?0:5);return vm!=nullptr;}
API(value) u32 value(u32 n){const u32 words[]={vm->layer,vm->flags2&0x400,float_bits(vm->position.x),float_bits(vm->position.y),float_bits(vm->position.z),float_bits(vm->rotation.z),u32(vm->pending_interrupt)};return words[n];}
API(update_case) i32 update_case(i32 kind,i32 sub,i32 clock,i32 replay,i32 continues,float rate,i32 selected,u32 pressed,u32 repeat){
 setup(0);if(!menu->begin(replay))return -1;initial_kind=kind;manager->rate=rate;menu->state=kind;menu->th16_substate=sub;menu->continues=continues;menu->cursor={};menu->cursor.count=5;menu->cursor.selected=menu->cursor.previous=selected;menu->cursor.wrap=1;
 if(sub==8||((sub==7||sub==9)&&clock>20)){menu->cursor.count=2;menu->cursor.depth=1;menu->cursor.selections[0]=4;menu->cursor.counts[0]=5;}
 menu->timer.set(clock,&manager->rate);menu->elapsed.set(clock,&manager->rate);return menu->update(pressed,repeat);
}
API(update_word) u32 update_word(u32 n){
 const auto& t=menu->timer;const auto& e=menu->elapsed;const auto& c=menu->cursor;
 const u32 words[]={u32(menu->state),u32(menu->th16_substate),u32(t.previous),u32(t.current),float_bits(t.fractional),t.flags,u32(e.previous),u32(e.current),float_bits(e.fractional),e.flags,u32(c.selected),u32(c.previous),u32(c.count),u32(c.wrap),u32(c.disabled_count)};
 if(n<15)return words[n];if(n<31)return u32(c.disabled[n-15]);if(n<33){auto* vm=manager->find(n==31?menu->menu_animation:menu->background_animation);return vm?u32(vm->pending_interrupt):0;}
 if(n==33)return initial_kind==1&&menu->state==0&&menu->action!=PauseAction::None;
 if(n==34)return c.depth;if(n<51)return c.selections[n-35];if(n<67)return c.counts[n-51];return u32(menu->action);
}
API(end_case) i32 end_case(i32 selection,i32 difficulty,u32 score,i32 continues,i32 remaining,i32 sub,i32 clock,float rate,i32 last,i32 selected,i32 length,u32 pressed,u32 repeat){
 setup(0);if(!menu->begin_end())return -1;first_creation=anm_creation_count();
 for(auto& record:scores.th16_characters)ScoreFile::th16_initialize_character(record);
 std::memcpy(scores.th16_last_name.data(),last?"AB      ":"        ",9);menu->selection=selection;menu->difficulty=difficulty;menu->result_score=signed_bits(score);menu->continues=continues;menu->th16_continues_remaining=remaining;menu->timestamp=0x123456789abcdef0ull;
 manager->rate=rate;menu->th16_substate=sub;menu->cursor.count=5;menu->cursor.wrap=1;
 if(sub==15){menu->cursor.selected=menu->cursor.previous=2;menu->cursor.count=25;menu->name_cursor.selected=menu->name_cursor.previous=selected;menu->name_cursor.count=91;menu->name_cursor.wrap=1;menu->name_length=length;std::memset(menu->entered_name.data(),' ',8);std::memcpy(menu->entered_name.data(),"ABCDEFGH",length);menu->entered_name[8]=0;}
 menu->timer.set(clock,&manager->rate);menu->elapsed.set(clock,&manager->rate);return menu->update(pressed,repeat);
}
API(end_word) u32 end_word(u32 n){
 if(n<31)return update_word(n);const auto& c=menu->name_cursor;
 const u32 words[]={u32(c.selected),u32(c.previous),u32(c.count),u32(c.wrap),u32(menu->name_length),u32(menu->unranked)};
 if(n<37)return words[n-31];if(n<46)return u8(menu->entered_name[n-37]);
 auto* vm=manager->find(n==46?menu->menu_animation:menu->background_animation);return vm?u32(vm->pending_interrupt):0;
}
API(end_rows) const u8* end_rows(){return scores.th16_characters[menu->selection].data()+0x10;}
API(end_last_name) const char* end_last_name(){return scores.th16_last_name.data();}
API(text_case) void text_case(i32 sub,i32 rank,i32 selected,i32 length,i32 unranked,i32 dated,i32 credits){
 end_case(0,0,50000,0,credits,15,0,1,0,selected,length,0,0);menu->th16_substate=sub;menu->cursor.selected=rank;menu->unranked=unranked;
 if(dated){auto* row=scores.th16_characters[0].data()+0x10+rank*32;const u64 timestamp=86400;std::memcpy(row+16,&timestamp,8);row[4]=9;row[5]=2;}
 ascii.clear();menu->queue_ascii(ascii);
}
API(text_count) u32 text_count(){return ascii.requests.size();}
API(text_string) const char* text_string(u32 n){return ascii.requests[n].text.c_str();}
API(text_word) u32 text_word(u32 n,u32 field){const auto& r=ascii.requests[n];const u32 words[]={float_bits(r.position.x),float_bits(r.position.y),float_bits(r.position.z),r.style.color};return words[field];}
