#include "../../cpp/game/PauseMenu.hpp"
#include "../../cpp/game/ReplayRecorder.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;
static AnmResource text,front,ascii;
static ScoreFile scores;
static std::unique_ptr<PauseMenu> menu;
static std::unique_ptr<AsciiText> output;
static std::array<std::shared_ptr<ReplayMenuEntry>,25> catalog{};
API(allocate) u8* allocate(u32 size){return static_cast<u8*>(std::malloc(size));}
API(setup) void setup(i32 state,i32 timer,i32 selected,i32 length,i32 glyph,i32 unranked,i32 selection,i32 difficulty,i32 stage,i32 credits,const u8* header,const u8* records){
    menu=std::make_unique<PauseMenu>(manager,text,front,scores);scores={};menu->replay_files=catalog;
    menu->state=state;menu->timer.set(timer,&manager.rate);menu->cursor.selected=selected;menu->name_length=length;menu->name_cursor.selected=glyph;menu->unranked=unranked;
    menu->selection=selection;menu->difficulty=difficulty;menu->stage=stage;std::memcpy(menu->entered_name.data(),"ABCDEFGH",9);
    std::memcpy(scores.characters[selection].data()+0x10+difficulty*0x118,records,280);
    if(state==10||state==17||state==24){u32 character,subtype,diff,id;std::memcpy(&menu->timestamp,header+12,8);std::memcpy(&character,header+0x7c,4);std::memcpy(&subtype,header+0x80,4);std::memcpy(&diff,header+0x84,4);std::memcpy(&id,header+0x90,4);menu->selection=character*2+subtype;menu->difficulty=diff;menu->spell_practice_id=header[10]&2?i32(id):-1;}
    if(state==14){menu->difficulty=3;menu->continues=5-credits;}
}
API(entry) u32 entry(u32 index,const u8* header){
    if(index>=25)return 0;if(!header){catalog[index].reset();return 1;}
    ReplayRecorder writer;if(!writer.begin(0,0,0,false,0))return 0;std::memcpy(writer.header.data(),header,writer.header.size());ReplayStageState state{};
    if(!writer.start_stage(1,state,true)||!writer.tick(0,0,0)||!writer.finish_stage())return 0;
    auto entry=std::make_shared<ReplayMenuEntry>();u32 score,reach,continues;float slowdown;std::memcpy(&score,header+0x14,4);std::memcpy(&reach,header+0x88,4);std::memcpy(&continues,header+0x8c,4);std::memcpy(&slowdown,header+0x74,4);
    if(!writer.save(reinterpret_cast<const char*>(header),signed_bits(score),signed_bits(reach),signed_bits(continues),slowdown,entry->file)||!entry->replay.open(entry->file.data(),u32(entry->file.size())))return 0;
    catalog[index]=std::move(entry);return 1;
}
API(queue) u32 queue(){output=std::make_unique<AsciiText>(ascii);menu->queue_ascii(*output);return output->requests.size();}
API(bytes) const char* bytes(u32 n){return output->requests[n].text.c_str();}
API(value) u32 value(u32 n,u32 k){const auto& r=output->requests[n];const float f[]={r.position.x,r.position.y,r.position.z,r.style.scale.x,r.style.scale.y};u32 word=0;if(k<3)std::memcpy(&word,&f[k],4);else if(k==3)word=r.style.color;else if(k==4)word=r.style.shadow;else if(k==5)word=r.style.font;else if(k<8)std::memcpy(&word,&f[k-3],4);return word;}
