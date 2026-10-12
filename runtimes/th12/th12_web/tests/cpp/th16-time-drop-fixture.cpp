#include "../../cpp/game/EnemyManager.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static EnemyState e;static EnemyEnvironment env;static EnemyCommandEnvironment commands;
API(setter) i32 setter(u32 flags,i32 duration,i32 count,i32 minimum){
 e={};e.th16_time_drop_timer.previous=31;e.th16_time_drop_timer.current=32;e.th16_time_drop_timer.fractional=20.5f;e.th16_time_drop_timer.flags=flags;e.th16_time_drop_timer.rate=&env.rate;
 e.th16_time_drop_duration=99;e.drops.counts[15]=77;e.th16_time_drop_minimum=55;
 alignas(4) u8 bytes[28]{};auto* cmd=reinterpret_cast<EclInstruction*>(bytes);cmd->opcode=1000;cmd->length=28;
 const i32 args[]={duration,count,minimum};std::memcpy(bytes+16,args,12);EclContext c;c.instruction=cmd;EnemyScriptServices services(e,env,commands);return services.command(c);
}
API(value) u32 value(u32 n){auto& t=e.th16_time_drop_timer;return n==0?u32(t.previous):n==1?u32(t.current):n==2?float_bits(t.fractional):n==3?t.flags:n==4?u32(e.th16_time_drop_duration):n==5?u32(e.drops.counts[15]):u32(e.th16_time_drop_minimum);}
API(tick) void tick(float rate,i32 current,float fraction){env.rate=rate;e.th16_time_drop_timer.previous=99;e.th16_time_drop_timer.current=current;e.th16_time_drop_timer.fractional=fraction;e.th16_time_drop_timer.rate=&env.rate;enemy_th16_time_drop_tick(e);}
API(decay) i32 decay(i32 duration,i32 current,i32 amount,i32 minimum){e.th16_time_drop_duration=duration;e.th16_time_drop_timer.current=current;e.drops.counts[15]=amount;e.th16_time_drop_minimum=minimum;return enemy_th16_time_drop_decay(e);}
API(damage_setter) i32 damage_setter(i32 total,i32 step){
 e={};e.th16_damage_total=total;e.th16_damage_drop_step=7;e.th16_damage_drop_next=9;
 alignas(4) u8 bytes[20]{};auto* cmd=reinterpret_cast<EclInstruction*>(bytes);cmd->opcode=1001;cmd->length=20;std::memcpy(bytes+16,&step,4);EclContext c;c.instruction=cmd;EnemyScriptServices services(e,env,commands);return services.command(c);
}
API(damage_word) u32 damage_word(u32 n){return n==0?u32(e.th16_damage_total):n==1?u32(e.th16_damage_drop_step):u32(e.th16_damage_drop_next);}
API(damage_case) void damage_case(u32 flags,i32 amount,i32 total){e={};e.health=997;e.max_health=1000;e.interrupt_health=100;e.scaled_health=6979;e.health_baseline=101;e.th16_damage_total=total;e.health_flags=flags;e.take_damage(amount);}
API(health_word) u32 health_word(u32 n){return n==0?u32(e.health):n==1?u32(e.scaled_health):u32(e.th16_damage_total);}
API(health_setter) i32 health_setter(u32 flags,i32 health){
 e={};e.flags=flags;alignas(4) u8 bytes[20]{};auto* cmd=reinterpret_cast<EclInstruction*>(bytes);cmd->opcode=511;cmd->length=20;std::memcpy(bytes+16,&health,4);EclContext c;c.instruction=cmd;EnemyScriptServices services(e,env,commands);return services.command(c);
}
API(health_set_word) u32 health_set_word(u32 n){const u32 words[]={u32(e.health),u32(e.max_health),u32(e.interrupt_health),u32(e.scaled_health),e.flags};return words[n];}
API(immunity_setter) i32 immunity_setter(u32 flags,i32 duration){
 e={};e.damage_immunity.previous=31;e.damage_immunity.current=32;e.damage_immunity.fractional=20.5f;e.damage_immunity.flags=flags;e.damage_immunity.rate=&env.rate;
 alignas(4) u8 bytes[20]{};auto* cmd=reinterpret_cast<EclInstruction*>(bytes);cmd->opcode=515;cmd->length=20;std::memcpy(bytes+16,&duration,4);EclContext c;c.instruction=cmd;EnemyScriptServices services(e,env,commands);return services.command(c);
}
API(immunity_word) u32 immunity_word(u32 n){auto& t=e.damage_immunity;return n==0?u32(t.previous):n==1?u32(t.current):n==2?float_bits(t.fractional):t.flags;}
