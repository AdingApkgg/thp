#include "../../cpp/game/EnemyScript.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static EnemyState enemy;static EnemyEnvironment environment;static EnemyCommandEnvironment commands;static bool sound;
API(run) u32 run(u32 ratio,i32 damage,i32 active){
 enemy={};alignas(4) u8 bytes[20]{};auto* ins=reinterpret_cast<EclInstruction*>(bytes);ins->opcode=565;ins->length=20;std::memcpy(bytes+16,&ratio,4);
 EclContext c;c.instruction=ins;EnemyScriptServices services(enemy,environment,commands);if(services.command(c)!=0)return 0x12345678;
 return u32(enemy_th14_bomb_damage(enemy,damage,active,sound));
}
API(sound_requested) u32 sound_requested(){return sound;}
API(ratio_value) u32 ratio_value(){return float_bits(enemy.th14_bomb_damage_ratio);}
API(default_ratio) u32 default_ratio(){enemy.initialize(nullptr,&environment.rate);return float_bits(enemy.th14_bomb_damage_ratio);}
API(default_hit_sound) i32 default_hit_sound(){enemy.initialize(nullptr,&environment.rate);return enemy.damage_reserved;}
API(hit_sound) i32 hit_sound(i32 override,u32 flags,u32 spell,i32 health){
 enemy={};enemy.flags=flags;enemy.interrupt_health=health;
 alignas(4) u8 bytes[20]{};auto* ins=reinterpret_cast<EclInstruction*>(bytes);ins->opcode=553;ins->length=20;std::memcpy(bytes+16,&override,4);
 EclContext c;c.instruction=ins;EnemyScriptServices services(enemy,environment,commands);if(services.command(c))return -999;
 return enemy_th14_hit_sound(enemy,spell);
}
