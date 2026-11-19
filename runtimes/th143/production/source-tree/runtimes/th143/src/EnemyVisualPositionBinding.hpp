#pragma once
#include "EnemyScripts.hpp"
#include <functional>
namespace th143 {
void bind_enemy_visual_positions(EnemyScripts&,std::function<AnmView(u32)>,std::function<float()>);
bool position_enemy_visuals(EnemyScripts&,ActorState&);
}
