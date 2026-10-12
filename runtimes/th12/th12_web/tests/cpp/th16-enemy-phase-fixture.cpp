#include "../../cpp/game/EnemyManager.hpp"
#include "../../cpp/game/ScreenDeformation.hpp"
#include <vector>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static EnemyState e;static EnemyEnvironment env;static EnemyCommandEnvironment world;
struct Deformation final:DeformationControl{
 std::vector<u32> events;
 bool release_deformation(EnemyState& enemy)override{events.push_back(0);enemy.deformation=nullptr;return true;}
 bool create_deformation(EnemyState& enemy)override{events.push_back(17);enemy.deformation=reinterpret_cast<ScreenDeformation*>(17);return true;}
} deformation;
alignas(4) static u8 bytes[128];
static i32 command(u16 op,const u32* args,u32 n,u32 offset=0,const char* name=nullptr){
 std::memset(bytes,0,sizeof(bytes));auto* cmd=reinterpret_cast<EclInstruction*>(bytes);cmd->opcode=op;cmd->length=sizeof(bytes);
 std::memcpy(bytes+16,args,n*4);if(name)std::strcpy(reinterpret_cast<char*>(bytes)+offset,name);
 EclContext c;c.instruction=cmd;EnemyScriptServices services(e,env,world);return services.command(c);
}
API(drop) i32 drop(u32 op,u32 a,u32 b){e={};const u32 args[]={a,b};return command(u16(op),args,2);}
API(phase_count) i32 phase_count(i32 value){world.remaining_phases=signed_bits(0xa5a5a5a5u);const u32 args[]={u32(value)};if(command(540,args,1)!=0)return INT32_MIN;return world.remaining_phases;}
API(drop_word) u32 drop_word(u32 n){return n==0?u32(e.drops.primary):n<18?u32(e.drops.counts[n-1]):n==18?float_bits(e.drops.spread.x):float_bits(e.drops.spread.y);}
API(marker) i32 marker(i32 boss,i32 index,i32 maximum,float amount,i32 kind){
 e={};world={};e.boss_slot=boss;e.max_health=maximum;const u32 args[]={u32(index),float_bits(amount),u32(kind)};return command(527,args,3);
}
API(marker_word) u32 marker_word(u32 n){const auto& s=world.th16_health_segments[n/8][n/2%4];return n&1?u32(s.type):float_bits(s.fraction);}
API(deformation_case) i32 deformation_case(i32 old,float target,u32 color){e={};world={};world.deformations=&deformation;deformation.events.clear();e.deformation=old?reinterpret_cast<ScreenDeformation*>(17):nullptr;const u32 args[]={float_bits(target),color};return command(629,args,2);}
API(deformation_word) u32 deformation_word(u32 n){const u32 v[]={u32(e.deformation!=nullptr),float_bits(e.deformation_target),float_bits(e.deformation_radius),e.deformation_color,float_bits(e.deformation_phase_x),float_bits(e.deformation_phase_y)};return v[n];}
API(deformation_event_count) u32 deformation_event_count(){return deformation.events.size();}
API(deformation_event) u32 deformation_event(u32 n){return deformation.events[n];}
API(interrupt_case) i32 interrupt_case(u32 op,i32 index,i32 health,i32 time,u32 name_kind){
 e={};world={};if(index<0||index>=8)return -2;
 auto& v=e.interrupts[index];v.health=37;v.time=99;
 std::strcpy(e.th16_interrupt_names[index][0],"old-health");std::strcpy(e.th16_interrupt_names[index][1],"old-timeout");
 v.health_script=e.th16_interrupt_names[index][0];v.timeout_script=e.th16_interrupt_names[index][1];
 char long_name[64];std::memset(long_name,'A',63);long_name[63]=0;
 const char* name=name_kind==0?"unused":name_kind==1?"":name_kind==2?"Boss01Nonspell01":long_name;
 const u32 args[]={u32(index),u32(health),u32(time)};const i32 result=command(u16(op),args,op==514?3:1,op==514?32:24,name);
 // The native consumers copy strings. Changing the instruction afterwards
 // must not change either stored transition name.
 std::memset(bytes+32,'Z',64);return result;
}
API(interrupt_word) u32 interrupt_word(u32 index,u32 n){return u32(n?e.interrupts[index].time:e.interrupts[index].health);}
API(interrupt_char) u32 interrupt_char(u32 index,u32 which,u32 n){const char* s=which?e.interrupts[index].timeout_script:e.interrupts[index].health_script;return u8(s[n]);}
static i32 seconds,hundredths,elapsed,bonus,shared,chapter,removed;static u32 spell_flags;
API(phase_case) i32 phase_case(u32 path,u32 index,i32 health,i32 clock,u32 flags,i32 credit,i32 chapter_value,u32 spellflags,i32 spell_elapsed,i32 special){
 e={};for(auto& v:e.interrupts)v.health=-1;
 for(u32 n=0;n<8;++n){e.interrupts[n].health_script=e.th16_interrupt_names[n][0];e.interrupts[n].timeout_script=e.th16_interrupt_names[n][1];}
 if(index<8){e.interrupts[index].health=100;e.interrupts[index].time=60;}
 e.health=health;e.interrupt_health=37;e.health_baseline=38;e.flags=flags;e.th16_chapter_tag=1;e.th16_chapter_credit=credit;
 auto& t=e.th16_phase_timer;t.previous=19;t.current=clock;t.fractional=float(double(clock)+.5);t.flags=0;t.rate=nullptr;
 seconds=17;hundredths=18;spell_flags=spellflags;elapsed=spell_elapsed;bonus=31;shared=37;chapter=chapter_value;removed=INT32_MAX;
 EnemyPhaseState state{&env.rate,&seconds,&hundredths,&spell_flags,&elapsed,&bonus,&shared,special,0,0,&chapter,&removed};
 const char* name=path?e.check_timed_interrupt16(state):e.check_health_interrupt16(state);
 if(!name)return 0;for(u32 n=0;n<8;++n)if(name==(path?e.interrupts[n].timeout_script:e.interrupts[n].health_script))return n+1;return -2;
}
API(phase_word) u32 phase_word(u32 n){
 const auto& t=e.th16_phase_timer;const u32 words[]={u32(e.health),u32(e.interrupt_health),u32(e.health_baseline),e.flags,u32(e.th16_chapter_credit),u32(t.previous),u32(t.current),float_bits(t.fractional),u32(bool(t.rate)),t.flags,u32(seconds),u32(hundredths),spell_flags,u32(bonus),u32(shared),u32(removed)};
 return n<16?words[n]:u32(e.interrupts[n-16].health);
}
