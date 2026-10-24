#include "../../cpp/game/EnemyCommands.hpp"
#include "../../cpp/game/AnmVm.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static EnemyState enemy;static AnmVm vm;static i32 sound;
API(run) void run(u32 flags,i32 lifetime,i32 flash,u32 spell,i32 health,u32 mode){
 enemy={};vm={};enemy.flags=flags;enemy.lifetime.current=lifetime;enemy.damage_flash=flash;
 enemy.damage_reserved=-1;enemy.interrupt_health=health;vm.th13_native_flags=mode;vm.secondary_color=0x12345678;
 sound=enemy_th14_hit_flash(enemy,vm,spell);
}
API(value) u32 value(u32 n){switch(n){case 0:return u32(enemy.damage_flash);case 1:return vm.th13_native_flags;case 2:return vm.secondary_color;default:return u32(sound);}}
