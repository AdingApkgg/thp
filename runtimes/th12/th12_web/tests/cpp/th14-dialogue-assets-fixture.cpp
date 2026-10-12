#include "../../cpp/game/Dialogue.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static i32 file,script;
API(asset) i32 asset(i32 stage,i32 selection,u32 opcode){file=script=123456;return Dialogue::th14_asset(stage,selection,opcode,file,script);}
API(word) u32 word(u32 n){return u32(n?script:file);}
static AnmManager manager;
static AnmResource resources[16];
static EnemyAnimations animations(manager);
struct Effects:DialogueEffects{u32 count=0,value=0;bool dialogue_fade(float f)override{++count;value=float_bits(f);return true;}};
static Effects effects;
static AnmVm* created;
static u32 ownership[13];
API(route) i32 route(i32 stage,i32 selection,u32 opcode){
 manager.clear();created=nullptr;effects.count=effects.value=0;
 for(u32 f=0;f<16;++f){resources[f]={};resources[f].scripts.resize(40);for(auto& s:resources[f].scripts){s.bytes.resize(16);const AnmInstruction h[]={ {i16(anm_canonical_opcode(2)),8,0,0},{-1,8,0,0}};std::memcpy(s.bytes.data(),h,16);}animations.resources[f]={&resources[f],u16(100+f)};}
 Dialogue d(manager,resources[0],resources[1],resources[2],resources[3],resources[4],effects);d.stage=stage;d.th14_animations=&animations;
 std::vector<u8> bytes(24);const u32 table[]={1,12,0};std::memcpy(bytes.data(),table,12);bytes[14]=u8(opcode);bytes[15]=4;std::memcpy(bytes.data()+16,&selection,4);bytes[20]=1;
 if(!d.begin(bytes,0))return -3;u32 initial[4];std::memcpy(initial,d.state.animations+3,sizeof initial);const auto result=d.update(0,0);created=manager.find(opcode==2||opcode==31?d.th14_enemy_portraits[opcode==31?1:selection]:d.state.animations[7]);
 const u32 handles[]={d.state.animations[0],d.th14_enemy_portraits[0],d.th14_enemy_portraits[1],d.th14_enemy_portraits[2],d.th14_enemy_portraits[3],d.state.animations[2],d.state.animations[3],d.state.animations[4],d.state.animations[5],d.state.animations[6],d.state.animations[7],d.th14_text_background,0};for(u32 i=0;i<13;++i)ownership[i]=created&&handles[i]==created->id?100:handles[i]&&(i<6||i>9||handles[i]!=initial[i-6])?0xffffffff:0;return result;
}
API(ownership_word) u32 ownership_word(u32 n){return n<13?ownership[n]:0xffffffff;}
API(created_word) u32 created_word(u32 n){if(!created)return 0xffffffff;switch(n){case 0:return created->file_index;case 1:return u32(created->script_index);case 2:return created->flags2&0x200;case 3:return created->layer;default:return created->resource==&resources[created->file_index-100];}}
API(fade_word) u32 fade_word(u32 n){return n?effects.value:effects.count;}
static u32 reset_words[29];
API(speaker_reset) i32 speaker_reset(i32 selection,u32 flags,u32 displacement){
 manager.clear();
 for(auto& r:resources){r={};r.scripts.resize(40);for(auto& s:r.scripts){s.bytes.resize(16);const AnmInstruction h[]={{i16(anm_canonical_opcode(2)),8,0,0},{-1,8,0,0}};std::memcpy(s.bytes.data(),h,16);}}
 Dialogue d(manager,resources[0],resources[1],resources[2],resources[3],resources[4],effects);
 std::vector<u8> bytes(24);const u32 table[]={1,12,0};std::memcpy(bytes.data(),table,12);bytes[14]=32;bytes[15]=4;std::memcpy(bytes.data()+16,&selection,4);bytes[20]=1;
 if(!d.begin(bytes,0))return -3;
 auto* portrait=manager.create(resources[0],0,0,22);if(!portrait)return -4;d.state.animations[2]=portrait->id;
 d.state.flags=flags;d.state.next_line=17;d.state.lines_initialized=19;
 for(u32 n=0;n<4;++n){auto* vm=manager.find(d.state.animations[3+n]);u32 words[]={0x3f000000+n,displacement,0x40000000+n,0x42c80000+n,0x43480000+n,0x43960000+n};std::memcpy(&vm->child_position,words,12);std::memcpy(&vm->position,words+3,12);}
 const auto result=d.update(0,0);reset_words[0]=d.state.speaker;reset_words[1]=d.state.flags;reset_words[2]=d.state.next_line;reset_words[3]=d.state.lines_initialized;reset_words[4]=portrait->pending_interrupt;
 for(u32 n=0;n<4;++n){auto* vm=manager.find(d.state.animations[3+n]);std::memcpy(reset_words+5+n*6,&vm->child_position,12);std::memcpy(reset_words+8+n*6,&vm->position,12);}
 return result;
}
API(reset_word) u32 reset_word(u32 n){return n<29?reset_words[n]:0xffffffff;}
