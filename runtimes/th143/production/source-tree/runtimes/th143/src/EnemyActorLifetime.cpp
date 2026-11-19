#include "EnemyActorLifetime.hpp"
#include <map>
namespace th143 {
namespace {std::map<EnemyScripts*,EnemyActorLifetime*> owners;}
void bind_enemy_actor_lifetime(EnemyScripts& s,EnemyActorLifetime* p){if(p)owners[&s]=p;else owners.erase(&s);}
bool begin_enemy_actor_retirement(EnemyScripts& s,EnemyScripts::Actor& a){auto i=owners.find(&s);return i!=owners.end()&&i->second->before_retirement(a);}
bool finish_enemy_actor_retirement(EnemyScripts& s,EnemyScripts::Actor& a){auto i=owners.find(&s);return i!=owners.end()&&i->second->after_retirement(a);}
}
