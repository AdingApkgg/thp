#include "PlayerBombScene.hpp"
namespace th143 {
bool PlayerBombScene::update(AnmView option,AnmView equipment,PlayerState* player,AnmView cheat,PlayerBombGlobals& g,const u32& special_flags,AnmWorld& world){
    if(flags)return false;flags=&special_flags;
    const bool okay=update_player_bomb(option,equipment,player,cheat,g,world,*this);flags=nullptr;return okay;
}
bool PlayerBombScene::bomb_bullets(AnmView position,float radius){
    return flags&&cancellation.circle({position.floating(0),position.floating(4),position.floating(8)},radius,0,false,*flags);
}
}
