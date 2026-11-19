#pragma once
#include "EnemyScripts.hpp"
namespace th143 {
struct EnemyActorLifetime {
 virtual ~EnemyActorLifetime()=default;
 virtual bool before_retirement(EnemyScripts::Actor&)=0;
 virtual bool after_retirement(EnemyScripts::Actor&)=0;
};
void bind_enemy_actor_lifetime(EnemyScripts&,EnemyActorLifetime*);
bool begin_enemy_actor_retirement(EnemyScripts&,EnemyScripts::Actor&);
bool finish_enemy_actor_retirement(EnemyScripts&,EnemyScripts::Actor&);
}
