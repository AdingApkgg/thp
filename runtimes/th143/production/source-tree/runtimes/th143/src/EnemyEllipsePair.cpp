#include "EnemyEllipsePair.hpp"
namespace th143 {
bool sample_enemy_ellipse_pair(AnmView slot,AnmTimerHost& rates,std::array<u32,2>& result){return anm_interpolate_vec2(slot,rates,result);}
}
