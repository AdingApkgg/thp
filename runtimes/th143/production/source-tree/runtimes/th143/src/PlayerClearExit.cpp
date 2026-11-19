#include "PlayerClearExit.hpp"
namespace th143 {
bool begin_player_clear_exit(PlayerState& player,PlayerClearExitHost& host){
 player.put(0x1847c,player.get(0x1847c)|1u);
 for(u32 i=0;i<8;++i){const u32 at=0xd79c+i*0xe4;if(!host.clear_exit_signal(player.get(at),3)||!host.clear_exit_signal(player.get(at+4),3))return false;}
 player.put(0x182c0,0);return true;
}
}
