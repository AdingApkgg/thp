#include "../../cpp/game/Dialogue.hpp"
#include "../../cpp/game/GameSessionResources.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static GameResources source;static GameSessionResources resources;static AnmManager manager;static EnemyAnimations animations(manager);
static std::string diagnostic;static std::unique_ptr<Dialogue> dialogue;static u32 writes,panels;static u32 masks[2];
struct Effects:DialogueEffects{
 bool dialogue_text(const DialogueText& r)override{++writes;if(r.style>=0&&r.style<8)masks[0]|=1u<<r.style;auto* vm=manager.find(r.animation);if(!vm){diagnostic="missing text VM";return false;}if(!vm->sprite){diagnostic="text VM has no sprite";return false;}return true;}
 bool dialogue_sound(i32)override{return true;}bool dialogue_music()override{return true;}bool dialogue_fade(float)override{return true;}bool dialogue_stage_complete()override{return true;}
};static Effects effects;
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(open_archive) i32 open_archive(const u8* p,u32 n){resources.animation_manager=&manager;if(!source.open_archive(p,n)||!resources.load_core(source)){diagnostic=resources.error.empty()?source.error():resources.error;return 0;}return 1;}
API(load_stage) i32 load_stage(u32 stage){dialogue.reset();manager.clear();if(!resources.load_stage(source,stage)){diagnostic=resources.error;return 0;}for(u32 i=0;i<4;++i)animations.resources[2+i]={resources.stage->ecl_animation_names[i].empty()?nullptr:&resources.stage->ecl_animations[i],u16(10+i)};return 1;}
API(entries) u32 entries(u32 selection){const auto& msg=resources.stage->messages[selection];u32 count=0;if(msg.size()>=4)std::memcpy(&count,msg.data(),4);return count;}
API(run) i32 run(u32 selection,i32 id){
 manager.clear();diagnostic.clear();writes=panels=0;masks[0]=masks[1]=0;
 dialogue=std::make_unique<Dialogue>(manager,resources.core.text,resources.core.players[selection/2],resources.core.front,resources.stage->enemies,resources.stage->logo,effects);dialogue->character=selection/2;dialogue->stage=resources.stage_number;dialogue->th14_animations=&animations;
 if(!dialogue->begin(resources.stage->messages[selection],id)){diagnostic=dialogue->error;return -1;}
 u32 last=0;
 for(u32 frame=0;frame<20000;++frame){const auto result=dialogue->update(0,0x80001);if(result<0){diagnostic=dialogue->error;return -2;}
  if(dialogue->th14_text_background!=last){if(dialogue->th14_text_background){++panels;masks[1]|=1u<<dialogue->th14_text_layout;}last=dialogue->th14_text_background;}
  if(!manager.update(false)||!manager.update(true)){diagnostic=manager.last_error_text();return -3;}
  if(result==1)return i32(frame+1);
 }diagnostic="dialogue exceeds 20000 frames";return -4;
}
API(value) u32 value(u32 n){return n==0?writes:n==1?panels:n==2?masks[0]:masks[1];}
API(error) const char* error(){return diagnostic.c_str();}
API(opcode) i32 opcode(){return dialogue?dialogue->last_opcode:-1;}
