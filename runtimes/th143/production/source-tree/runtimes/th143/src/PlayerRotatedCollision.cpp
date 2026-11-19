#include "PlayerRotatedCollision.hpp"
#include <cmath>
namespace th143 {
i32 player_rotated_rectangle_probe(PlayerState& player,const std::array<float,3>& origin,float length,float width,float angle,bool centered){
    const float dx=player.floating(0x5e0)-origin[0],dy=player.floating(0x5e4)-origin[1];
    const float sine=float(std::sin(double(-angle))),cosine=float(std::cos(double(-angle)));
    const float local_y=cosine*dy+sine*dx,local_x=cosine*dx-sine*dy;
    const float hx=player.floating(0x648),hy=player.floating(0x64c);
    const float outer_min_x=local_x-hx*16.f,outer_min_y=local_y-hy*16.f;
    const float outer_max_x=local_x+hx*16.f,outer_max_y=local_y+hy*16.f;
    const float right=centered?length*.5f:length,left=centered?length*-.5f:0.f,top=width*-.5f,bottom=width*.5f;
    // Original JA rejection does not reject unordered comparisons.
    if(outer_min_x>right||outer_min_y>bottom||left>outer_max_x||top>outer_max_y)return 0;
    const float inner_min_x=local_x-hx,inner_min_y=local_y-hy,inner_max_x=local_x+hx,inner_max_y=local_y+hy;
    if(inner_min_x>right||inner_min_y>bottom||left>inner_max_x||top>inner_max_y)return 2;
    return 1;
}
i32 player_rotated_rectangle_collision(PlayerState& player,bool blocked,const std::array<float,3>& origin,float length,float width,float angle,bool forced,PlayerHitHost& host,bool centered){
    const i32 result=player_rotated_rectangle_probe(player,origin,length,width,angle,centered);if(result!=1)return result;
    if((player.get(0x1847c)&0x20)||blocked)return 0;
    if(forced)return 2;
    const u32 state=player.get(0x684);if(state==2||state==4||state==3||signed_word(player.get(0x1846c))>0)return 0;
    return host.hit(player)?1:-2;
}
}
