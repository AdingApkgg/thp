#include "../../cpp/game/EnemyState.hpp"
#include <array>
using namespace th11;
static std::array<Enemy,64> enemies{};
static EnemyLink* head=nullptr;
static EnemyEnvironment environment{};
static EnemyState owner{};
static EnemyGlobals globals(owner,environment);
#define API(name) extern "C" __attribute__((export_name(#name)))
API(reset) void reset(u32 n){head=n?&enemies[0].state.manager_link:nullptr;environment.th14_enemy_list=&head;for(u32 i=0;i<n;++i){auto& e=enemies[i];e.state={};e.state.manager_link.value=&e;e.state.manager_link.next=i+1<n?&enemies[i+1].state.manager_link:nullptr;}}
API(set_enemy) void set_enemy(u32 i,u32 flags,i32 immunity){enemies[i].state.flags=flags;enemies[i].state.damage_immunity.current=immunity;}
API(count_integer) i32 count_integer(){return globals.integer(-9908);}
API(count_float) u32 count_float(){return float_bits(float(globals.floating(-9908)));}
