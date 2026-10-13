#include "../../cpp/game/EnemyCommands.hpp"
#include "../../cpp/game/Dialogue.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static EnemyState enemy;
static EnemyEnvironment environment;
static EnemyGlobals globals(enemy,environment);
static EnemyCommandEnvironment world;
static void* field(u32 n){
    void* fixed[]={&enemy.flags,&enemy.hitbox.x,&enemy.hitbox.y,&enemy.collision_box.x,&enemy.collision_box.y,
        &enemy.clamp_center.x,&enemy.clamp_center.y,&enemy.clamp_size.x,&enemy.clamp_size.y,
        &enemy.health,&enemy.max_health,&enemy.interrupt_health,&enemy.scaled_health,&enemy.drops.primary};
    if(n<14)return fixed[n];if(n<27)return enemy.drops.counts+n-14;
    if(n==27)return &enemy.drops.spread.x;if(n==28)return &enemy.drops.spread.y;
    return n==29?&world.stage_section:&world.section_frame;
}
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(run) i32 run(u32 op,u32 n,const u32* input,const u32* args){
    enemy={};world={};for(u32 i=0;i<29;++i)std::memcpy(field(i),input+i,4);
    for(u32 i=13;i<19;++i)enemy.drops.counts[i]=123456;
    world.stage_section=n%3;world.section_frame=100+n;
    alignas(4) u8 bytes[32]{};auto* cmd=reinterpret_cast<EclInstruction*>(bytes);cmd->opcode=u16(op);cmd->length=32;std::memcpy(bytes+16,args,16);
    EclContext context;context.instruction=cmd;const auto result=enemy_th14_state_command(enemy,context,globals,world);
    for(u32 i=13;i<19;++i)if(enemy.drops.counts[i]!=123456)return -3;return result;
}
API(value) u32 value(u32 n){u32 v;std::memcpy(&v,field(n),4);return v;}
static EnemyState peers[16];
alignas(4) static u8 phase_instruction[48];
static const char* old_health="old_health";
static const char* old_timeout="old_timeout";
API(interrupt_case) i32 interrupt_case(u32 slot,i32 health,i32 time){
    enemy={};world={};enemy.interrupts[slot]={100,200,old_health,old_timeout};
    std::memset(phase_instruction,0,sizeof phase_instruction);auto* cmd=reinterpret_cast<EclInstruction*>(phase_instruction);cmd->opcode=514;cmd->length=48;
    const i32 args[]={i32(slot),health,time};std::memcpy(phase_instruction+16,args,12);std::memcpy(phase_instruction+32,"next_phase",11);
    EclContext context;context.instruction=cmd;return enemy_th14_state_command(enemy,context,globals,world);
}
API(interrupt_value) u32 interrupt_value(u32 slot,u32 n){auto& v=enemy.interrupts[slot];return n==0?u32(v.health):n==1?u32(v.time):n==2?(v.health_script==reinterpret_cast<char*>(phase_instruction+32)?1:2):(v.timeout_script==reinterpret_cast<char*>(phase_instruction+32)?1:3);}
API(timeout_name_case) i32 timeout_name_case(u32 slot){
    enemy={};world={};enemy.interrupts[slot]={100,200,old_health,old_timeout};
    std::memset(phase_instruction,0,sizeof phase_instruction);auto* cmd=reinterpret_cast<EclInstruction*>(phase_instruction);cmd->opcode=521;cmd->length=48;
    std::memcpy(phase_instruction+16,&slot,4);std::memcpy(phase_instruction+24,"next_timeout",13);
    EclContext c;c.instruction=cmd;return enemy_th14_state_command(enemy,c,globals,world);
}
API(timeout_name_value) u32 timeout_name_value(u32 slot,u32 n){auto& v=enemy.interrupts[slot];return n==0?u32(v.health):n==1?u32(v.time):n==2?2:(v.timeout_script==reinterpret_cast<char*>(phase_instruction+24)?1:3);}
API(mark_case) i32 mark_case(u32 boss,u32 slot,i32 health,float value,u32 type){
    enemy={};world={};enemy.max_health=health;enemy.boss_slot=i32(boss);
    alignas(4) u8 bytes[28]{};auto* cmd=reinterpret_cast<EclInstruction*>(bytes);cmd->opcode=527;cmd->length=28;const u32 args[]={slot,float_bits(value),type};std::memcpy(bytes+16,args,12);
    EclContext context;context.instruction=cmd;return enemy_th14_state_command(enemy,context,globals,world);
}
API(mark_value) u32 mark_value(u32 boss,u32 slot,u32 n){auto& v=world.th14_health_segments[boss][slot];return n?u32(v.type):float_bits(v.fraction);}
static float alternative_rate=.5f;
API(timer_case) i32 timer_case(u32 flags,u32 pointer){
    enemy={};enemy.timer_2bc={111,222,333.5f,pointer==0?nullptr:pointer==1?&alternative_rate:&environment.rate,flags};
    EclInstruction cmd{};cmd.opcode=513;EclContext context;context.instruction=&cmd;return enemy_th14_state_command(enemy,context,globals,world);
}
API(timer_value) u32 timer_value(u32 n){auto& t=enemy.timer_2bc;switch(n){case 0:return u32(t.previous);case 1:return u32(t.current);case 2:return float_bits(t.fractional);case 3:return t.flags;default:return !t.rate?0:t.rate==&alternative_rate?1:2;}}
API(boss_case) i32 boss_case(u32 flags,u32 manager_flags,i32 selected,i32 prior){
    enemy={};world={};enemy.flags=flags;enemy.boss_slot=prior;world.manager_flags=manager_flags;
    for(u32 n=0;n<world.boss_capacity;++n)world.bosses[n]=(flags&0x800000)&&i32(n)==prior?&enemy:&peers[n];
    alignas(4) u8 bytes[20]{};auto* cmd=reinterpret_cast<EclInstruction*>(bytes);cmd->opcode=512;cmd->length=20;std::memcpy(bytes+16,&selected,4);
    EclContext context;context.instruction=cmd;return enemy_th14_state_command(enemy,context,globals,world);
}
API(boss_value) u32 boss_value(u32 n){
    if(n==0)return enemy.flags;if(n==1)return u32(enemy.boss_slot);if(n==2)return world.manager_flags;
    auto* p=world.bosses[n-3];return !p?0:p==&enemy?1:n-1;
}
API(boss_global) i32 boss_global(){return environment.boss==world.bosses[0];}
API(boss_wait) i32 boss_wait(u32 pattern){
    world={};for(u32 n=0;n<8;++n)world.bosses[n]=pattern&(1u<<n)?&peers[n]:nullptr;
    EclInstruction cmd{};cmd.opcode=520;cmd.length=16;EclContext c;c.instruction=&cmd;
    return enemy_th14_state_command(enemy,c,globals,world);
}
struct WaitDialogue:DialogueControl{
    bool waiting=false;
    bool start_dialogue(i32)override{return false;}
    bool dialogue_waiting()const override{return waiting;}
};
API(dialogue_wait) i32 dialogue_wait(u32 present,u32 signal){
    WaitDialogue d;d.waiting=!signal;world={};world.dialogue=present?&d:nullptr;
    EclInstruction cmd{};cmd.opcode=519;cmd.length=16;EclContext c;c.instruction=&cmd;
    return enemy_th14_state_command(enemy,c,globals,world);
}
API(phase_count) u32 phase_count(i32 value){
    world={};world.remaining_phases=37;
    alignas(4) u8 bytes[20]{};auto* cmd=reinterpret_cast<EclInstruction*>(bytes);cmd->opcode=540;cmd->length=20;std::memcpy(bytes+16,&value,4);
    EclContext c;c.instruction=cmd;
    if(enemy_th14_state_command(enemy,c,globals,world))return 0xdeadbeef;
    return u32(world.remaining_phases);
}
API(clear_tick_callback) i32 clear_tick_callback(u32 prior,i32 mode,i32 index){
    enemy.tick_callback=EnemyTick(prior);enemy.callbacks[0]=mode;
    alignas(4) u8 bytes[20]{};auto* cmd=reinterpret_cast<EclInstruction*>(bytes);cmd->opcode=632;cmd->length=20;std::memcpy(bytes+16,&index,4);
    EclContext c;c.instruction=cmd;return enemy_th14_state_command(enemy,c,globals,world);
}
API(tick_callback_word) u32 tick_callback_word(u32 n){return n?u32(enemy.callbacks[0]):u32(enemy.tick_callback);}
API(health_flag_case) u32 health_flag_case(u32 flags,i32 value,u32 refs){
    enemy={};enemy.health_flags=flags;enemy.integers[0]=value;world={};
    alignas(4) u8 bytes[20]{};auto* cmd=reinterpret_cast<EclInstruction*>(bytes);cmd->opcode=568;cmd->length=20;cmd->references=u16(refs);
    const i32 arg=refs?64:value;std::memcpy(bytes+16,&arg,4);EclContext c;c.instruction=cmd;c.stack.frame_base=32;std::memcpy(c.stack.data+96,&value,4);
    return enemy_th14_state_command(enemy,c,globals,world)==0?enemy.health_flags:0xdeadbeef;
}
API(assign) u32 assign(u32 op,i32 difficulty,const u32* args){
    environment.difficulty=difficulty;
    alignas(4) u8 bytes[36]{};auto* cmd=reinterpret_cast<EclInstruction*>(bytes);cmd->opcode=u16(op);cmd->length=36;cmd->references=1;std::memcpy(bytes+16,args,20);
    EclContext context;context.instruction=cmd;context.stack.frame_base=32;const u32 initial=0x12345678;std::memcpy(context.stack.data+96,&initial,4);
    if(enemy_th14_state_command(enemy,context,globals,world))return 0xdeadbeef;
    return context.stack.local<u32>(64);
}

API(death_sound_case) u32 death_sound_case(i32 value){
 enemy={};world={};enemy.damage_reserved=123;alignas(4) u8 bytes[20]{};auto* ins=reinterpret_cast<EclInstruction*>(bytes);ins->opcode=553;ins->length=20;std::memcpy(bytes+16,&value,4);
 EclContext c;c.instruction=ins;return enemy_th14_state_command(enemy,c,globals,world)==0?u32(enemy.damage_reserved):0x12345678;
}
API(rewind_case) u32 rewind_case(i32 difficulty,u32 time,const u32* counts,u32 refs){
 environment.difficulty=difficulty;
 alignas(4) u8 bytes[32]{};auto* ins=reinterpret_cast<EclInstruction*>(bytes);ins->opcode=548;ins->length=32;ins->references=u16(refs);
 EclContext c;c.instruction=ins;c.time=float_bits(time);c.stack.frame_base=32;
 for(u32 n=0;n<4;++n){const u32 offset=n*4;std::memcpy(bytes+16+n*4,refs?&offset:counts+n,4);std::memcpy(c.stack.data+32+n*4,counts+n,4);}
 return enemy_th14_state_command(enemy,c,globals,world)==0?float_bits(c.time):0x12345678;
}
static float rate_target;
API(rate_case) i32 rate_case(u32 value,u32 refs,u32 connected){
 environment.rate=rate_target=float_bits(0x12345678u);world.th14_rate_target=connected?&rate_target:nullptr;
 alignas(4) u8 bytes[20]{};auto* ins=reinterpret_cast<EclInstruction*>(bytes);ins->opcode=547;ins->length=20;ins->references=u16(refs);
 EclContext c;c.instruction=ins;c.stack.frame_base=32;const u32 offset=0;std::memcpy(bytes+16,refs?&offset:&value,4);std::memcpy(c.stack.data+32,&value,4);
 return enemy_th14_state_command(enemy,c,globals,world);
}
API(rate_word) u32 rate_word(u32 n){return float_bits(n?rate_target:environment.rate);}
API(hitbox_angle_case) u32 hitbox_angle_case(u32 value,u32 refs){
 enemy={};world={};alignas(4) u8 bytes[20]{};auto* ins=reinterpret_cast<EclInstruction*>(bytes);ins->opcode=564;ins->length=20;ins->references=u16(refs);
 EclContext c;c.instruction=ins;c.stack.frame_base=32;const u32 offset=0;std::memcpy(bytes+16,refs?&offset:&value,4);std::memcpy(c.stack.data+32,&value,4);
 return enemy_th14_state_command(enemy,c,globals,world)==0?float_bits(enemy.animation_angle):0x12345678;
}
