#pragma once
#include "EnemyScripts.hpp"
namespace th143 {
void bind_enemy_animation_scratch(EnemyScripts&,std::array<u32,2>*,u32 caller_ebx);
void bind_enemy_curve_scratch(EnemyScripts&,u32*);
void enemy_animation_stack_entry(EnemyScripts&);
void enemy_animation_stack_lookup(EnemyScripts&,u32 handle);
void enemy_animation_stack_lookup(EnemyScripts&,u32 handle,bool direct);
}
