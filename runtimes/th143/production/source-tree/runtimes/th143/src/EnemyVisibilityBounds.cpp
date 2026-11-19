#include "EnemyVisibilityBounds.hpp"
namespace th143 {
i32 update_enemy_visibility_bounds(AnmView s){
 const u32 flags=s.get(0x4100);const float x=s.floating(0x44),y=s.floating(0x48),hx=s.floating(0x3ffc)*.5f,hy=s.floating(0x4000)*.5f;
 // Ordered greater-than tests match COMISS/JA, including unordered inputs.
 // The original handles an X rejection before considering a Y rejection.
 if(-192.f>x+hx||x-hx>192.f)return (flags&0x10000)&&!(flags&4)?-1:0;
 if(0.f>y+hy||y-hy>448.f)return (flags&0x10000)&&!(flags&8)?-1:0;
 s.put(0x4100,flags|0x10000);return 0;
}
}
