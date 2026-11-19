#include "EnemyEllipseAdvance.hpp"
namespace th143 {
namespace {float wrap(float v){u32 count=0;while(v>real(0x40490fdb)){v-=real(0x40c90fdb);if(count++>32)break;}while(real(0xc0490fdb)>v){v+=real(0x40c90fdb);if(count++>32)break;}return v;}}
bool advance_enemy_ellipse(AnmView p,float rate){p.put(0x20,word(p.floating(0x24)*rate+p.floating(0x20)));p.put(0x1c,word(wrap(p.floating(0x18)*rate+p.floating(0x1c))));return evaluate_enemy_ellipse(p);}
}
