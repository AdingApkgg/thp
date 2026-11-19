#include "PlayerDraw.hpp"
namespace th143 {
bool draw_player(PlayerState& player,u32 self,PlayerDrawHost& host){
    if(player.get(0x684)==2)return true;
    for(u32 i=0;i<3;++i)player.put(0x5b0+i*4,player.get(0x5e0+i*4));
    player.put(0x30,(player.get(0x30)&~0x40000u)|0x20000u);
    return (player.get(0x1847c)&0x80)||host.draw_player_visual(self+0x14,{player.data.data()+0x14});
}
}
