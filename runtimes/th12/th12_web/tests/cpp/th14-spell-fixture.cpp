#include "../../cpp/game/SpellController.hpp"
#include "../../cpp/game/EnemyFrame.hpp"
#include "../../cpp/game/SpellTh14Visuals.hpp"
#include "../../cpp/game/AnmOpcodes.hpp"
#include "../../cpp/game/EnemyManager.hpp"
#include <cstdlib>
#include <vector>
using namespace th11;
#define EXPORT extern "C" __attribute__((visibility("default")))
namespace {
struct World final:EnemyFrameWorld {void clear_shot_targets(Enemy*)override{}};
std::vector<u32> state,record,sounds,titles,timers,closed,result;
struct Effects final:SpellEffects {
    u32 background=0;Vec3 circle{};
    bool spell_begin_visuals(i32 id,i32 duration,const char* name)override{result={u32(id),u32(duration)};for(const auto* p=reinterpret_cast<const u8*>(name);*p;++p)closed.push_back(*p);return true;}
    bool spell_update_visuals()override{std::abort();}
    void spell_background(bool hidden)override{background=hidden?background|1:background&~1u;}
    void spell_title_interrupt(i16 label)override{for(int n=0;n<3;++n)titles.push_back(u32(label));}
    void spell_circle_position(Vec3 p)override{circle=p;}
    void spell_circle_end()override{closed.push_back(0x20);}
    bool spell_result(bool captured,i32 bonus)override{result.push_back(captured);result.push_back(u32(bonus));return true;}
    bool spell_sound(i32 id)override{sounds.push_back(u32(id));return true;}
    bool spell_timer_interrupt(i16 label)override{timers.push_back(label);timers.push_back(label);return true;}
    void spell_background_end()override{closed.push_back(0x10);}
};
void reset(){state.clear();record.clear();sounds.clear();titles.clear();timers.clear();closed.clear();result.clear();}
void seed(SpellRecords& r,i32 selection,i32 id,const u32* words){for(i32 n=0;n<2;++n){auto& a=r.entries[n?6:selection][id];a.captures=signed_bits(words[n*4]);a.practice_captures=signed_bits(words[n*4+1]);a.attempts=signed_bits(words[n*4+2]);a.practice_attempts=signed_bits(words[n*4+3]);}}
void records(const SpellRecords& r,i32 selection,i32 id){for(i32 n=0;n<2;++n){const auto& a=r.entries[n?6:selection][id];record.insert(record.end(),{u32(a.captures),u32(a.practice_captures),u32(a.attempts),u32(a.practice_attempts)});}}
void save(const EnemyFrameWorld& w,const SpellController& c){state={w.spell_flags,u32(w.spell_id),u32(w.spell_bonus),u32(c.initial_bonus),u32(c.timeout),u32(c.frame_count),u32(c.timer.previous),u32(c.timer.current),float_bits(c.timer.fractional),c.timer.flags,float_bits(c.circle_position.x),float_bits(c.circle_position.y),float_bits(c.circle_position.z)};}
}
EXPORT void* allocate(u32 n){return std::malloc(n);} EXPORT void release(void* p){std::free(p);}
extern "C" __attribute__((export_name("invalidate"))) u32 invalidate(u32 flags){World w;GameEconomy e;Effects fx;SpellRecords r;float speed=1;SpellController spell(w,e,fx,r,&speed);w.spell_flags=flags;EnemyState enemy;EnemyEnvironment env;EnemyCommandEnvironment commands;commands.spells=&spell;EnemyScriptServices services(enemy,env,commands);
 EclInstruction ins{};ins.opcode=542;ins.length=16;EclContext c;c.instruction=&ins;return services.command(c)==0?w.spell_flags:0x12345678;}
extern "C" __attribute__((export_name("orientation"))) u32 orientation(u32 flags,i32 value){World w;GameEconomy e;Effects fx;SpellRecords r;float speed=1;SpellController spell(w,e,fx,r,&speed);w.spell_flags=flags;EnemyState enemy;EnemyEnvironment env;EnemyGlobals g(enemy,env);EnemyCommandEnvironment world;world.spells=&spell;
 alignas(4) u8 bytes[20]{};auto* ins=reinterpret_cast<EclInstruction*>(bytes);ins->opcode=567;ins->length=20;std::memcpy(bytes+16,&value,4);EclContext c;c.instruction=ins;return enemy_th14_state_command(enemy,c,g,world)==0?w.spell_flags:0x12345678;}
EXPORT i32 begin(const u32* a){reset();World w;GameEconomy e;Effects fx;SpellRecords r;float speed=1;SpellController c(w,e,fx,r,&speed);
    w.spell_flags=a[5];e.difficulty=signed_bits(a[4]);c.selection=signed_bits(a[2]);c.stage=signed_bits(a[3]);c.run_flags=a[6];c.replay=a[8];c.timer.flags=a[9];seed(r,c.selection,signed_bits(a[0]),a+10);
    bool ok=c.begin(signed_bits(a[0]),signed_bits(a[1]),"Native spell",{12.25,-14.5,4.75},a[7]==1);save(w,c);records(r,c.selection,signed_bits(a[0]));return ok;}
EXPORT i32 update(const u32* a){reset();World w;GameEconomy e;Effects fx;SpellRecords r;float speed=float_bits(a[2]);SpellController c(w,e,fx,r,&speed);
    w.spell_flags=a[0];w.spell_bonus=signed_bits(a[4]);c.initial_bonus=signed_bits(a[5]);c.timeout=signed_bits(a[6]);c.frame_count=123;c.timer.set(signed_bits(a[1]),&speed);c.timer.fractional=float(double(c.timer.current)+.25);c.circle_position={12.25,-14.5,4.75};fx.background=0x81;
    bool ok=c.update(float_bits(a[3]),{-33.125,144.25,-9.5},a[7]==1);save(w,c);record={fx.background,float_bits(fx.circle.x),float_bits(fx.circle.y),float_bits(fx.circle.z)};return ok;}
EXPORT i32 end(const u32* a){reset();World w;GameEconomy e;Effects fx;SpellRecords r;float speed=1;SpellController c(w,e,fx,r,&speed);
    w.spell_flags=a[0];w.spell_id=2;w.spell_bonus=signed_bits(a[4]);c.selection=signed_bits(a[5]);c.run_flags=a[1];c.replay=a[2];e.score_units=signed_bits(a[3]);seed(r,c.selection,2,a+6);
    bool ok=c.end();state={w.spell_flags,u32(e.score_units),fx.background};records(r,c.selection,2);return ok;}
EXPORT i32 end_command(const u32* a,u32 health_flags){reset();World w;GameEconomy e;Effects fx;SpellRecords r;EnemyEnvironment environment;SpellController spell(w,e,fx,r,&environment.rate);
    w.spell_flags=a[0];w.spell_id=2;w.spell_bonus=signed_bits(a[4]);spell.selection=signed_bits(a[5]);spell.run_flags=a[1];spell.replay=a[2];e.score_units=signed_bits(a[3]);seed(r,spell.selection,2,a+6);
    EnemyState enemy;enemy.health_flags=health_flags;EnemyCommandEnvironment commands;commands.spells=&spell;EclProgram program;EnemyManager manager(program,environment,commands,w);
    EclInstruction instruction{};instruction.opcode=523;instruction.length=16;EclContext context;context.instruction=&instruction;EnemyScriptServices services(enemy,environment,commands);
    const i32 ok=services.command(context);state={w.spell_flags,u32(e.score_units),fx.background,enemy.health_flags};records(r,spell.selection,2);return ok;}
EXPORT u32 value(u32 group,u32 index){const auto& values=group==0?state:group==1?record:group==2?sounds:group==3?titles:group==4?timers:group==5?closed:result;return index<values.size()?values[index]:0xffffffff;}
EXPORT u32 count(u32 group){const auto& values=group==0?state:group==1?record:group==2?sounds:group==3?titles:group==4?timers:group==5?closed:result;return values.size();}
EXPORT i32 factory(const u32* a){reset();AnmManager manager;EnemyAnimations files(manager);AnmResource resources[7];
    auto append=[](AnmResource& r,u32 index,i16 raw,i32 argument=0){auto& b=r.scripts[index].bytes;auto at=b.size();u32 bytes=raw==500?4:0;b.resize(at+8+bytes);AnmInstruction h{raw==-1?i16(-1):i16(anm_canonical_opcode(raw)),u16(8+bytes),0,0};std::memcpy(b.data()+at,&h,8);if(bytes)std::memcpy(b.data()+at+8,&argument,4);};
    for(auto& r:resources){r.scripts.resize(32);for(u32 n=0;n<32;++n){if(&r==resources+2&&n==13){append(r,n,500,11);append(r,n,500,12);}append(r,n,2);append(r,n,-1);}}
    for(u32 n=0;n<4;++n)files.resources[n+2]={resources+3+n,u16(10+n)};
    u32 ids[3]{},circle=0,bg=0;const u32 first=anm_creation_count();
    bool ok=spell_th14_create_visuals(manager,files,resources[0],resources[1],resources[2],signed_bits(a[0]),signed_bits(a[1]),signed_bits(a[2]),2400,{12.25,-14.5,4.75},ids,circle,bg,[](u32){return true;},[](i32 id){sounds.push_back(u32(id));return true;});
    for(u32 n=first;n<anm_creation_count();++n)if(!anm_creation_value(n,4)){auto* vm=manager.find(u32(anm_creation_value(n,5)));if(!vm)return -3;
        state.insert(state.end(),{u32(vm->file_index),u32(vm->script_index),vm->flags2&0x200,float_bits(vm->position.x),float_bits(vm->position.y),float_bits(vm->position.z),float_bits(vm->rotation.z)});}
    if(auto* vm=manager.find(circle))for(i32 script:{11,12})for(auto* n=vm->child.next;n;n=n->next)if(n->value->script_index==script)record.push_back(u32(n->value->integers[2]));
    return ok;
}
EXPORT i32 command(const u8* bytes,u32 size,i32 difficulty,i32 health,u32 flags,u32 mode){reset();alignas(4) u8 instruction[128]{};if(size>sizeof instruction)return -3;std::memcpy(instruction,bytes,size);
    World w;GameEconomy economy;Effects fx;SpellRecords records;EnemyEnvironment environment;EnemyState enemy,boss;EnemyCommandEnvironment commands;SpellController spell(w,economy,fx,records,&environment.rate);
    environment.difficulty=difficulty;enemy.health=health;enemy.health_flags=flags;enemy.timer_2bc.flags=mode;enemy.timer_2bc.rate=mode?&environment.rate:nullptr;commands.bosses[0]=&boss;commands.spells=&spell;
    EclContext c;c.instruction=reinterpret_cast<const EclInstruction*>(instruction);EnemyGlobals globals(enemy,environment);
    const auto answer=enemy_th14_state_command(enemy,c,globals,commands);state={enemy.health_flags,u32(enemy.scaled_health),u32(enemy.timer_2bc.previous),u32(enemy.timer_2bc.current),float_bits(enemy.timer_2bc.fractional),enemy.timer_2bc.flags};return answer;
}
